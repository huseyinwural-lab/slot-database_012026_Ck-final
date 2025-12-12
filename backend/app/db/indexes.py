import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
  """Create required indexes in an idempotent way.

  This should be called on application startup. Failures are logged but
  do not prevent the app from starting.
  """

  # Players
  try:
      await db.players.create_index(
          [("tenant_id", 1), ("registered_at", -1)],
          name="idx_players_tenant_registered_at",
      )
      logger.info("ensure_indexes: players.idx_players_tenant_registered_at created/existed")
  except Exception as exc:
      logger.warning("ensure_indexes: players.idx_players_tenant_registered_at failed: %s", exc)

  # Transactions
  try:
      await db.transactions.create_index(
          [("tenant_id", 1), ("created_at", -1)],
          name="idx_tx_tenant_created_at",
      )
      logger.info("ensure_indexes: transactions.idx_tx_tenant_created_at created/existed")
  except Exception as exc:
      logger.warning("ensure_indexes: transactions.idx_tx_tenant_created_at failed: %s", exc)

  # Games
  try:
      await db.games.create_index(
          [("tenant_id", 1), ("created_at", -1)],
          name="idx_games_tenant_created_at",
      )
      logger.info("ensure_indexes: games.idx_games_tenant_created_at created/existed")
  except Exception as exc:
      logger.warning("ensure_indexes: games.idx_games_tenant_created_at failed: %s", exc)

  # Tenants
  try:
      await db.tenants.create_index(
          [("created_at", -1)],
          name="idx_tenants_created_at",
      )
      logger.info("ensure_indexes: tenants.idx_tenants_created_at created/existed")
  except Exception as exc:
      logger.warning("ensure_indexes: tenants.idx_tenants_created_at failed: %s", exc)
