from collections.abc import Iterable


class TreeAccessPermissions:
    """Per-tree membership capabilities (cascading like system RBAC)."""

    VIEW = "view"
    EDIT = "edit"
    ADD_PERSONS = "add_persons"

    ALL: tuple[str, ...] = (VIEW, EDIT, ADD_PERSONS)

    # Selecting a capability also requires these.
    REQUIREMENTS: dict[str, tuple[str, ...]] = {
        EDIT: (VIEW,),
        ADD_PERSONS: (VIEW,),
    }

    LABELS_FA: dict[str, str] = {
        VIEW: "دیدن",
        EDIT: "تغییر",
        ADD_PERSONS: "اضافه کردن افراد",
    }

    LABELS_EN: dict[str, str] = {
        VIEW: "View",
        EDIT: "Edit",
        ADD_PERSONS: "Add people",
    }

    @classmethod
    def get_all(cls) -> list[str]:
        return list(cls.ALL)

    @classmethod
    def is_known(cls, name: str) -> bool:
        return name in cls.ALL

    @classmethod
    def get_direct_requirements(cls, permission_name: str) -> tuple[str, ...]:
        return cls.REQUIREMENTS.get(permission_name, ())

    @classmethod
    def expand_with_requirements(cls, permission_names: Iterable[str]) -> set[str]:
        result = set(permission_names)
        queue = list(result)
        while queue:
            current = queue.pop()
            for required in cls.get_direct_requirements(current):
                if required not in result:
                    result.add(required)
                    queue.append(required)
        return result

    @classmethod
    def normalize(cls, permission_names: Iterable[str]) -> list[str]:
        """Expand prerequisites and return a stable sorted list of known names."""
        known = {name for name in permission_names if cls.is_known(name)}
        if not known:
            known = {cls.VIEW}
        return sorted(cls.expand_with_requirements(known))
