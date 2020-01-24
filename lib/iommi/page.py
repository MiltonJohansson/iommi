from typing import (
    Dict,
    List,
    Optional,
    Type,
    Any,
)

from django.utils.html import format_html
from iommi._web_compat import (
    Template,
)
from iommi.base import (
    PagePart,
    PartType,
    bind_members,
    collect_members,
    no_copy_on_bind,
    as_html,
    evaluate_attrs,
)
from iommi.render import render_attrs
from tri_declarative import (
    EMPTY,
    Namespace,
    Refinable,
    declarative,
    dispatch,
    with_meta,
)


# https://html.spec.whatwg.org/multipage/syntax.html#void-elements
_void_elements = ['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr']


def fragment__render(fragment, context):
    rendered_children = fragment.render_text_or_children(context=context)

    is_void_element = fragment.tag in _void_elements

    if fragment.tag:
        if rendered_children:
            assert not is_void_element
            return format_html(
                '<{tag}{attrs}>{children}</{tag}>',
                tag=fragment.tag,
                attrs=render_attrs(fragment.attrs),
                children=rendered_children,
            )
        else:
            return format_html(
                '<{tag}{attrs}>' if is_void_element else '<{tag}{attrs}></{tag}>',
                tag=fragment.tag,
                attrs=render_attrs(fragment.attrs),
            )

    else:
        return format_html(
            '{}',
            rendered_children,
        )


class Fragment(PagePart):
    attrs: Dict[str, Any] = Refinable()
    tag = Refinable()

    @dispatch(
        attrs=EMPTY,
        tag=None,
    )
    def __init__(self, child: PartType = None, *, children: Optional[List[PartType]] = None, **kwargs):
        super(Fragment, self).__init__(**kwargs)

        self._children = []  # TODO: _children to avoid colliding with PageParts children() API. Not nice. We should do something nicer here.
        if child is not None:
            self._children.append(child)

        self._children.extend(children or [])

    def render_text_or_children(self, context):
        return format_html(
            '{}' * len(self._children),
            *[
                as_html(part=x, context=context)
                for x in self._children
            ])

    def __getitem__(self, item):
        if isinstance(item, tuple):
            self._children.extend(item)
        else:
            self._children.append(item)
        return self

    def __repr__(self):
        return f'<Fragment: tag:{self.tag}, attrs:{self.attrs}>'

    def on_bind(self) -> None:
        self.attrs = evaluate_attrs(self.attrs, **self._evaluate_attribute_kwargs())

    @dispatch(
        context=EMPTY,
        render=fragment__render,
    )
    def as_html(self, *, context=None, render=None):
        return render(fragment=self, context=context)

    def _evaluate_attribute_kwargs(self):
        return dict(page=self.parent, fragment=self)


@no_copy_on_bind
@with_meta
@declarative(
    parameter='_parts_dict',
    is_member=lambda obj: isinstance(obj, (PagePart, str, Template)),
    sort_key=lambda x: 0,
)
class Page(PagePart):
    member_class: Type[Fragment] = Refinable()

    class Meta:
        member_class = Fragment

    @dispatch(
        parts=EMPTY,
    )
    def __init__(
        self,
        *,
        _parts_dict: Dict[str, PartType] = None,
        parts: dict,
        **kwargs
    ):
        super(Page, self).__init__(**kwargs)
        
        self.parts = {}  # This is just so that the repr can survive if it gets triggered before parts is set properly

        # First we have to up sample parts that aren't PagePart into Fragment
        def as_fragment_if_needed(k, v):
            if not isinstance(v, PagePart):
                return Fragment(v, name=k)
            else:
                return v

        _parts_dict = {k: as_fragment_if_needed(k, v) for k, v in _parts_dict.items()}
        parts = Namespace({k: as_fragment_if_needed(k, v) for k, v in parts.items()})

        self._columns_unapplied_data = {}
        self.declared_parts: Dict[str, PartType] = collect_members(items=parts, items_dict=_parts_dict, cls=self.get_meta().member_class, unapplied_config=self._columns_unapplied_data)

    def on_bind(self) -> None:
        self.parts = bind_members(declared_items=self.declared_parts, parent=self)

    def __repr__(self):
        return f'<Page with parts: {list(self.parts.keys())}>'

    def children(self):
        if not self._is_bound:
            # TODO: hmm...
            self.bind(request=None)
        return self.parts

    def endpoint_kwargs(self):
        return dict(page=self)

    @dispatch(
        context=EMPTY,
        render=lambda rendered: format_html('{}' * len(rendered), *rendered.values())
    )
    def as_html(self, *, context=None, render=None):
        rendered = {}
        for part in self.parts.values():
            assert part.name not in context
            rendered[part.name] = as_html(part=part, context=context)

        return render(rendered)


class Html:
    def __getattr__(self, tag):
        def fragment_constructor(child: PartType = None, **kwargs):
            return Fragment(tag=tag, child=child, **kwargs)
        return fragment_constructor


html = Html()
