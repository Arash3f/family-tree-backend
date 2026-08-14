from dataclasses import dataclass
from uuid import UUID

from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.tree_excel_service import build_sample_workbook


@dataclass
class ExcelFileDTO:
    filename: str
    content: bytes
    media_type: str = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


class GetTreeExcelSampleUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, *, tree_id: UUID, lang: str = "en") -> ExcelFileDTO:
        locale = "fa" if lang == "fa" else "en"
        async with self.uow:
            await self.uow.family_trees.get_or_raise(tree_id)
        return ExcelFileDTO(
            filename=f"family-tree-sample-{locale}.xlsx",
            content=build_sample_workbook(lang=locale),
        )
