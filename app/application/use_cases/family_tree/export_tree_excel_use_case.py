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

        safe_name = (
            "".join(
                ch if (ch.isascii() and (ch.isalnum() or ch in ("-", "_"))) else "-"
                for ch in tree.name
            ).strip("-")
            or "family-tree"
        )

        return ExcelFileDTO(
            filename=f"{safe_name}-export-{locale}.xlsx",
            content=build_export_workbook(
                persons=persons, marriages=marriages, lang=locale
            ),
        )
