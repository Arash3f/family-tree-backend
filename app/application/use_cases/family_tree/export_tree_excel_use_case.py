import asyncio
from functools import partial
from uuid import UUID

from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.tree_excel_loader import (
    load_all_tree_marriages,
    load_all_tree_persons,
)
from app.application.services.tree_excel_service import build_export_workbook
from app.application.use_cases.family_tree.get_tree_excel_sample_use_case import (
    ExcelFileDTO,
)


class ExportTreeExcelUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, *, tree_id: UUID, lang: str = "en") -> ExcelFileDTO:
        locale = "fa" if lang == "fa" else "en"
        async with self.uow:
            tree = await self.uow.family_trees.get_or_raise(tree_id)
            persons = await load_all_tree_persons(self.uow, tree_id)
            marriages = await load_all_tree_marriages(self.uow, tree_id)

        # The tree name is kept as the user typed it; the router adds an ASCII
        # fallback next to the UTF-8 filename for older download clients.
        display_name = " ".join(tree.name.split()) or "family-tree"

        excel_content = await asyncio.get_event_loop().run_in_executor(
            None,
            partial(
                build_export_workbook,
                persons=persons,
                marriages=marriages,
                lang=locale,
            ),
        )

        suffix = "شجره‌نامه" if locale == "fa" else "export"
        return ExcelFileDTO(
            filename=f"{display_name}-{suffix}.xlsx",
            content=excel_content,
        )
