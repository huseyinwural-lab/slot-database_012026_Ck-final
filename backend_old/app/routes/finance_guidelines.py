from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/finance/chargebacks", tags=["finance_guidelines"])


@router.get("/guidelines")
async def get_represent_guidelines():
    # P0: static content for modal.
    return {
        "title": "Represent Guidelines",
        "sections": [
            {
                "heading": "What is representment?",
                "body": "Representment is the process of disputing a chargeback by submitting evidence to the card network / PSP.",
            },
            {
                "heading": "Common evidence",
                "body": "KYC verification, proof of deposit method ownership, device/IP history, session logs, transaction timeline, and player support communications.",
            },
            {
                "heading": "Operational checklist",
                "body": "1) Verify original deposit and gameplay logs\n2) Check KYC level and any risk flags\n3) Collect evidence links\n4) Submit before deadline\n5) Track outcome and update case status",
            },
        ],
    }
