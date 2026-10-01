import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import col, func, select

from app.api.deps import (
    CurrentWorkspace,
    CurrentWorkspaceEditor,
    SessionDep,
    get_current_workspace_editor,
)
from app.models import Item, ItemCreate, ItemPublic, ItemsPublic, ItemUpdate, Message

router = APIRouter(prefix="/items", tags=["items"])


def _item_in_workspace(*, item: Item | None, workspace_id: uuid.UUID) -> Item:
    if not item or item.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.get("/", response_model=ItemsPublic)
def read_items(
    session: SessionDep,
    workspace: CurrentWorkspace,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve items in the current workspace.
    """
    count = session.exec(
        select(func.count()).select_from(Item).where(Item.workspace_id == workspace.id)
    ).one()
    items = session.exec(
        select(Item)
        .where(Item.workspace_id == workspace.id)
        .order_by(col(Item.created_at).desc())
        .offset(skip)
        .limit(limit)
    ).all()
    return ItemsPublic(
        data=[ItemPublic.model_validate(item) for item in items],
        count=count,
    )


@router.get("/{id}", response_model=ItemPublic)
def read_item(session: SessionDep, workspace: CurrentWorkspace, id: uuid.UUID) -> Any:
    """
    Get item by ID.
    """
    return _item_in_workspace(item=session.get(Item, id), workspace_id=workspace.id)


@router.post("/", response_model=ItemPublic)
def create_item(
    *,
    session: SessionDep,
    current_user: CurrentWorkspaceEditor,
    workspace: CurrentWorkspace,
    item_in: ItemCreate,
) -> Any:
    """
    Create new item. Editor or Admin.
    """
    item = Item.model_validate(
        item_in, update={"owner_id": current_user.id, "workspace_id": workspace.id}
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.put(
    "/{id}",
    response_model=ItemPublic,
    dependencies=[Depends(get_current_workspace_editor)],
)
def update_item(
    *,
    session: SessionDep,
    workspace: CurrentWorkspace,
    id: uuid.UUID,
    item_in: ItemUpdate,
) -> Any:
    """
    Update an item. Editor or Admin.
    """
    item = _item_in_workspace(item=session.get(Item, id), workspace_id=workspace.id)
    update_dict = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_dict)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{id}", dependencies=[Depends(get_current_workspace_editor)])
def delete_item(
    session: SessionDep,
    workspace: CurrentWorkspace,
    id: uuid.UUID,
) -> Message:
    """
    Delete an item. Editor or Admin.
    """
    item = _item_in_workspace(item=session.get(Item, id), workspace_id=workspace.id)
    session.delete(item)
    session.commit()
    return Message(message="Item deleted successfully")
