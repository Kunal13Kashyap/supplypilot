"""Unit tests for deterministic replenishment."""

from app.rules.replenishment import ReplenishmentInput, calculate_replenishment


def test_golden_modify_400():
    result = calculate_replenishment(
        ReplenishmentInput(
            on_hand=300,
            inbound_open_po=200,
            lead_time_demand=700,
            target_stock=200,
            moq=100,
            unit_price=8,
            budget_remaining=4000,
            storage_additional=600,
            supplier_max_available=5000,
            original_recommended_qty=800,
        )
    )
    assert result.recommended_quantity == 400
    assert result.decision == "MODIFY"
    assert result.inventory_position == -200


def test_accept_matches_engine():
    result = calculate_replenishment(
        ReplenishmentInput(
            on_hand=50,
            inbound_open_po=0,
            lead_time_demand=150,
            target_stock=200,
            moq=10,
            unit_price=3,
            budget_remaining=20000,
            storage_additional=2000,
            supplier_max_available=5000,
            original_recommended_qty=300,
        )
    )
    assert result.recommended_quantity == 300
    assert result.decision == "ACCEPT"


def test_reject_budget_below_moq():
    result = calculate_replenishment(
        ReplenishmentInput(
            on_hand=100,
            inbound_open_po=0,
            lead_time_demand=500,
            target_stock=200,
            moq=100,
            unit_price=50,
            budget_remaining=1000,
            storage_additional=5000,
            supplier_max_available=5000,
            original_recommended_qty=600,
        )
    )
    assert result.decision == "REJECT"
    assert result.recommended_quantity == 0


def test_investigate_missing_moq():
    result = calculate_replenishment(
        ReplenishmentInput(
            on_hand=80,
            inbound_open_po=0,
            lead_time_demand=200,
            target_stock=200,
            moq=None,
            unit_price=12,
            budget_remaining=10000,
            storage_additional=1000,
            original_recommended_qty=200,
        )
    )
    assert result.decision == "INVESTIGATE"
