from django import template
from roundabout.parts.models import Part
from roundabout.locations.models import Location

register = template.Library()


@register.filter
def is_in(var, obj):
    return var in obj

@register.simple_tag
def define(val=None):
    return val

@register.simple_tag
def get_parts_list_by_type(type_pk):
    queryset = Part.objects.filter(part_type=type_pk)
    return queryset

@register.simple_tag
def get_parts_list_by_location(location_pk):
    queryset = Part.objects.filter(location=location_pk).filter(parent=None).prefetch_related('children')
    return queryset

@register.simple_tag
def get_parts_children(pk, location_pk):
    part = Part.objects.get(pk=pk)
    valid_parts = Part.objects.filter(location=location_pk)
    location = Location.objects.get(pk=location_pk)

    def descendants_by_location_tree(part, valid_parts):
        """
        Returns a tree-like structure with progeny for specific Location
        """
        tree = {}
        for f in part.children.all():
            if f in valid_parts:
                tree[f] = descendants_by_location_tree(f, valid_parts)
        return tree

    return descendants_by_location_tree(part, valid_parts)


class RecurseDictNode(template.Node):
    def __init__(self, var, nodeList):
        self.var = var
        self.nodeList = nodeList

    def __repr__(self):
        return '<RecurseDictNode>'

    def renderCallback(self, context, vals, level):
        if len(vals) == 0:
            return ''

        output = []

        if 'loop' in self.nodeList:
            output.append(self.nodeList['loop'].render(context))

        for k, v in vals:
            context.push()

            context['level'] = level
            context['key'] = k

            if 'value' in self.nodeList:
                output.append(self.nodeList['value'].render(context))

                if type(v) == list or type(v) == tuple:
                    child_items = [ (None, x) for x in v ]
                    output.append(self.renderCallback(context, child_items, level + 1))
                else:
                    try:
                        child_items = v.items()
                        output.append(self.renderCallback(context, child_items, level + 1))
                    except:
                        output.append(unicode(v))

            if 'endloop' in self.nodeList:
                output.append(self.nodeList['endloop'].render(context))
            else:
                output.append(self.nodeList['endrecursedict'].render(context))

            context.pop()

        if 'endloop' in self.nodeList:
            output.append(self.nodeList['endrecursedict'].render(context))

        return ''.join(output)

    def render(self, context):
        vals = self.var.resolve(context).items()
        output = self.renderCallback(context, vals, 1)
        return output


def recursedict_tag(parser, token):
    bits = list(token.split_contents())
    if len(bits) != 2 and bits[0] != 'recursedict':
        raise template.TemplateSyntaxError("Invalid tag syntax expected '{ recursedict [dictVar] %}'")

    var = parser.compile_filter(bits[1])
    nodeList = {}
    while len(nodeList) < 4:
        temp = parser.parse(('value','loop','endloop','endrecursedict'))
        tag = parser.tokens[0].contents
        nodeList[tag] = temp
        parser.delete_first_token()
        if tag == 'endrecursedict':
            break

    return RecurseDictNode(var, nodeList)

recursedict_tag = register.tag('recursedict', recursedict_tag)
