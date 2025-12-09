@router.put("/games/{game_id}/details")
async def update_game_details(game_id: str, details: Dict[str, Any] = Body(...)):
    db = get_db()
    # Log audit
    await db.audit_logs.insert_one({
        "admin_id": "current_admin",
        "action": "update_game_details",
        "target_id": game_id,
        "details": str(details),
        "timestamp": datetime.now(timezone.utc)
    })
    
    # Allowed fields to update
    allowed = ["name", "category", "provider", "image_url", "tags"]
    update_data = {k: v for k, v in details.items() if k in allowed}
    
    if not update_data:
        raise HTTPException(400, "No valid fields to update")

    res = await db.games.update_one({"id": game_id}, {"$set": update_data})
    if res.matched_count == 0:
        raise HTTPException(404, "Game not found")
        
    return {"message": "Game details updated"}
