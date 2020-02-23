"""Tree of dit classes and objects, represented by node objects."""
from typing import List
from dit_cli.exceptions import TreeError


class Node:
    """A dataclass which represents an node in the tree."""

    def __init__(self, name: str, type_: str):
        self.name: str = name
        self.type_: str = type_
        self.extends: List[int] = []
        # {name: str, prefix: str, id_: int, list_depth: int, data: ?}
        self.contains: List[dict] = []
        self.validator: str = None  # Code
        self.print: dict = None  # {code, variable}, only one populated
        self.conflicts: List[dict] = []  # {class_, var}


class Tree:
    """Stores a directed tree of Node objects.
    Each node is either a dit class or object.
    The connections between nodes represent extension or containment"""

    def __init__(self):
        self.nodes: List[Node] = []

    def new(self, name: str, type_: str) -> Node:
        """Add a blank node to this tree and return it"""
        for node in self.nodes:
            if name == node.name:
                raise TreeError(
                    f'Variable "{name}" has already been defined')
        self.nodes.append(Node(name, type_))
        return self.cur()

    def cur(self) -> Node:
        return self.nodes[-1]

    def add_extend(self, extend_name: str):
        id_ = _id_from_name(extend_name, self.nodes)
        if id_ in self.cur().extends:
            raise TreeError(
                f'"{self.cur().name}" already extends "{extend_name}"')

        for extend in self.cur().extends:
            for old_contain in self.nodes[extend].contains:
                for new_contain in self.nodes[id_].contains:
                    if old_contain['name'] == new_contain['name']:
                        self.cur().conflicts.append(
                            {'class_': extend_name, 'var': old_contain['name']})

        self.cur().extends.append(id_)

    def add_contain(self, type_name: str, var_name: str,
                    list_depth: int = None):
        if type_name == 'String':
            id_ = -1
        else:
            id_ = _id_from_name(type_name, self.nodes)

        for contain in self.cur().contains:
            if var_name == contain['name']:
                raise TreeError(
                    f'Variable "{var_name}" has already been defined')

        for extend in self.cur().extends:
            for old_contain in self.nodes[extend].contains:
                if old_contain['name'] == var_name:
                    self.cur().conflicts.append(
                        {'class_': self.nodes[extend].name, 'var': var_name})

        contain = {'id_': id_, 'name': var_name, 'list_depth': list_depth,
                   'data': None, 'prefix': None}
        self.cur().contains.append(contain)

    def set_print(self, variable: List[str] = None, code: str = None):
        # Make sure variable to be printed is defined
        if variable:
            _process_var(self, variable, class_=self.cur())

        self.cur().print = {'variable': variable, 'code': code}

    def set_validator(self, code: str):
        self.cur().validator = code

    def is_defined(self, variable: List[str]):
        _process_var(self, variable)

    def assign_var(self, variable: List[str], data):
        _process_var(self, variable, data=data)

    def get_node(self, variable: List[str]):
        return _process_var(self, variable)


class Assigner:
    """A dataclass which represents an assigner"""

    def __init__(self, name: str, id_: int):
        self.name: str = name
        self.id_: int = id_
        self.param_count: int = None
        self.assignments: List[dict] = []  # {variable, position}


class Assigners:
    """Stores the dit assigners for this parser"""

    def __init__(self):
        self.assigners: List[Assigner] = []

    def new(self, type_name: str, assigner_name: str, tree: Tree):
        id_ = _id_from_name(type_name, tree.nodes)

        if assigner_name in [func.name for func in self.assigners]:
            raise TreeError(
                f'Assigner "{assigner_name}" has already been defined')

        self.assigners.append(Assigner(assigner_name, id_))

    def cur(self) -> Assigner:
        return self.assigners[-1]

    def set_assign(self, raw_assigns: List[dict],
                   parameters: List[str], tree: Tree):

        for raw in raw_assigns:
            _process_var(tree, raw['variable'],
                         class_=tree.nodes[self.cur().id_])
            if raw['parameter'] not in parameters:
                raise TreeError(f'Undefined parameter "{raw["parameter"]}"')
            for (position, parameter) in enumerate(parameters):
                if parameter == raw['parameter']:
                    assignment = {'variable': raw['variable'],
                                  'position': position}
                    break

            self.cur().assignments.append(assignment)


def _process_var(tree: Tree, variable: List[str], class_: Node = None, data=None):

    if not class_:
        obj = tree.nodes[_id_from_name(variable[0], tree.nodes)]
        if obj.type_ == 'class':
            raise TreeError(f'Cannot assign to class: {variable[0]}')
        class_ = tree.nodes[obj.extends[0]]
        variable.pop(0)
    else:
        obj = None

    prefix = None
    for index, var in enumerate(variable):
        result = _recurse_var(var, class_, tree)
        if result[0] == 'not found':
            raise TreeError(f'Undefined variable "{var}" in "{variable}"')

        if index < len(variable) - 1:  # There are more elements
            if result[0] == 'extend':
                prefix = _get_prefix(variable[index + 1], result[1], result[2])
                class_ = result[1]
                continue
            elif result[0] == 'contain':
                class_contain = result[1]
                obj_contain = _find_contain(obj, var, prefix)
                if class_contain['id_'] == -1:
                    raise TreeError(
                        f'Cannot reference string "{var}" in "{variable}"')

                if data is not None and obj_contain is None:
                    new_obj = Node(var, 'object')
                    new_obj.extends.append(class_contain['id_'])
                    new_contain = class_contain.copy()
                    new_contain['data'] = new_obj
                    new_contain['prefix'] = prefix
                    obj.contains.append(new_contain)
                    obj = new_obj
                else:
                    obj = None if obj_contain is None else obj_contain['data']

                class_ = tree.nodes[class_contain['id_']]
                continue

        if result[0] == 'extend':
            if data:
                raise TreeError(f'Cannot assign to class: {var}')
            else:
                return result[1]
        elif result[0] == 'contain':
            contain = _find_contain(obj, var, prefix)
            if data is None and contain is None:
                return None
            elif data is None and contain is not None:
                return contain['data']
            elif data is not None and contain is None:
                new_contain = result[1].copy()
                new_contain['data'] = data
                new_contain['prefix'] = prefix
                obj.contains.append(new_contain)
                return
            elif data is not None and contain is not None:
                old_data = contain['data']
                contain['data'] = data
                return old_data
    return obj

    '''
    for index, var in enumerate(variable):
        result = _recurse_var(var, class_, tree)
        if result[0] == 'contain':
            contain = result[1]
            if index < len(variable) - 1:  # There are more elements
                if contain['id_'] == -1:
                    raise TreeError(
                        f'Cannot reference string "{var}" in "{variable}"')
                class_ = tree.nodes[contain['id_']]
            if data:
                found = _find_contain(obj, var, prefix)
                if index < len(variable) - 1:
                    if found is not None:
                        obj = obj.contains[found]['data']
                    else:
                        contain = contain.copy()
                        new_obj = Node(var, 'object')
                        new_obj.extends.append(contain['id_'])
                        contain['data'] = new_obj
                        contain['prefix'] = prefix
                        obj.contains.append(contain)
                        obj = new_obj
                else:
                    if found is not None:
                        obj.contains[found]['data'] = data
                    else:
                        contain = contain.copy()
                        contain['data'] = data
                        contain['prefix'] = prefix
                        obj.contains.append(contain)
            prefix = None
        elif result[0] == 'extend':
            extend = result[1]
            class_ = result[2]
            if index < len(variable) - 1:
                if class_.conflicts and data:
                    for con in class_.conflicts:
                        if (con['class_'] == extend.name and
                                con['var'] == variable[index + 1]):
                            prefix = extend.name + '.' + variable[index + 1]
                            break
                class_ = extend
            elif data:
                raise TreeError(
                    f'Cannot assign to class: {var}')
        elif result[0] == 'not found':
            raise TreeError(f'Undefined variable "{var}" in "{variable}"')
    '''


def _get_prefix(var: str, extend: Node, class_: Node) -> str:
    for con in class_.conflicts:
        if (con['class_'] == extend.name and con['var'] == var):
            return extend.name + '.' + var


def _find_contain(obj: Node, var: str, prefix: str) -> dict:
    if obj is None:
        return None
    for contain in obj.contains:
        if prefix:
            if prefix == contain['prefix']:
                return contain
        elif var == contain['name']:
            return contain
    return None


def _recurse_var(var: str, node: Node, tree: Tree):

    # Is var contained here, in this node?
    for contain in node.contains:
        if var == contain['name']:
            return ('contain', contain, node)

    for id_ in node.extends:
        extend = tree.nodes[id_]
        # Maybe it's an explicitly extended class?
        if extend.name == var:
            return ('extend', extend, node)
        else:
            # Or somewhere in an extended class?
            (enum, data, new_node) = _recurse_var(var, extend, tree)
            if enum != 'not found':
                return (enum, data, new_node)

    return ('not found', None, None)


def _id_from_name(name: str, nodes: List[Node]) -> int:
    """Find an node in a list that matches the given name."""
    for id_, node in enumerate(nodes):
        if node.name == name:
            return id_

    raise TreeError(f'Undefined variable "{name}"')
