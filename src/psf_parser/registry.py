from psf_parser.declaration import Section, Declaration, DeclarationId, GroupDeclaration


class Registry:

    def __init__(self):
        self.declarations: dict[DeclarationId, Declaration] = {}
        self._name_map: dict[tuple[Section, tuple[str, ...], str], Declaration] = {}
        self._next_id: int = 1

    def generate_id(self) -> int:
        decl_id = self._next_id
        self._next_id += 1
        return decl_id

    def add(self, decl: Declaration, scope: tuple[str, ...] = ()):
        name_map_key = (decl.section, scope, decl.name)

        if decl.id in self.declarations:
            raise ValueError(f'Error: Duplicate id: {decl.id}')
        if name_map_key in self._name_map:
            raise ValueError(f'Error: Duplicate scoped name: {decl.section.name}::{".".join(scope + (decl.name,))}')

        self.declarations[decl.id] = decl
        self._name_map[name_map_key] = decl

    def get_by_id(self, decl_id: DeclarationId) -> Declaration | None:
        return self.declarations.get(decl_id)

    def get_by_name(self, name: str, section: Section, scope: tuple[str, ...] = ()) -> Declaration | None:
        return self._name_map.get((section, scope, name))

    def get_by_flat_name(self, name: str) -> list[Declaration]:
        return [decl for scoped, decl in self._name_map.items() if scoped[-1] == name]

    @property
    def types(self):
        return [decl for decl in self.declarations.values() if decl.section is Section.TYPE]

    @property
    def sweeps(self):
        return [
            decl for decl in self.declarations.values()
            if decl.section is Section.SWEEP and not isinstance (decl, GroupDeclaration)
        ]

    @property
    def traces(self):
        return [
            decl for decl in self.declarations.values()
            if decl.section is Section.TRACE and not isinstance (decl, GroupDeclaration)
        ]

    @property
    def values(self):
        return [decl for decl in self.declarations.values() if decl.section is Section.VALUE]

    def __repr__(self):
        return f'<Registry: {len(self.types)} types, {len(self.sweeps)} sweeps, {len(self.traces)} traces, {len(self.values)} values>'
