from collections.abc import Iterable, Mapping

from sqlalchemy import String, asc, cast, desc, func, or_
from sqlalchemy.sql import ColumnElement
from sqlalchemy.sql.selectable import Select


def apply_exact_filter(statement: Select, column: ColumnElement, value: str | None) -> Select:
    if value is None:
        return statement
    return statement.where(column == value)


def apply_case_insensitive_filter(statement: Select, column: ColumnElement, value: str | None) -> Select:
    if value is None:
        return statement
    return statement.where(func.lower(cast(column, String)) == value.lower())


def apply_contains_filter(statement: Select, columns: Iterable[ColumnElement], search: str | None) -> Select:
    if search is None:
        return statement
    pattern = f"%{search.lower()}%"
    clauses = [func.lower(cast(column, String)).like(pattern) for column in columns]
    return statement.where(or_(*clauses)) if clauses else statement


def apply_json_path_filter(statement: Select, json_column: ColumnElement, json_path: str, value: str | None) -> Select:
    if value is None:
        return statement
    extracted = func.coalesce(func.json_extract(json_column, json_path), "")
    return statement.where(func.lower(cast(extracted, String)) == value.lower())


def apply_pagination(statement: Select, *, page: int, page_size: int) -> Select:
    return statement.offset(max(page - 1, 0) * page_size).limit(page_size)


def apply_sort(
    statement: Select,
    *,
    sort: str | None,
    allowed: Mapping[str, ColumnElement],
    default: str | None = None,
) -> Select:
    resolved_sort = (sort or default or "").strip()
    if not resolved_sort:
        return statement

    direction = desc if resolved_sort.startswith("-") else asc
    key = resolved_sort[1:] if resolved_sort.startswith("-") else resolved_sort
    column = allowed.get(key)
    if column is None:
        if default is not None and resolved_sort != default:
            return apply_sort(statement, sort=default, allowed=allowed, default=None)
        return statement
    return statement.order_by(direction(column))
