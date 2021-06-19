from typing import TypeVar, Optional, Callable, Dict

from mypy.nodes import NameExpr
from mypy.options import Options
from mypy.plugin import Plugin, DynamicClassDefContext

T = TypeVar('T')
CB = Optional[Callable[[T], None]]
DynamicClassDef = DynamicClassDefContext


class TinyDBPlugin(Plugin):
    def __init__(self, options: Options):
        super().__init__(options)

        self.named_placeholders: Dict[str, str] = {}

    def get_dynamic_class_hook(self, fullname: str) -> CB[DynamicClassDef]:
        if fullname == 'tinydb.utils.with_typehint':
            def hook(ctx: DynamicClassDefContext):
                klass = ctx.call.args[0]
                assert isinstance(klass, NameExpr)

                type_name = klass.fullname
                assert type_name is not None

                qualified = self.lookup_fully_qualified(type_name)
                assert qualified is not None

                ctx.api.add_symbol_table_node(ctx.name, qualified)

            return hook

        return None


def plugin(_version: str):
    return TinyDBPlugin
