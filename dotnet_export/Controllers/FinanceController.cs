using CasinoAdmin.Models;
using Microsoft.AspNetCore.Mvc;
using MongoDB.Driver;

namespace CasinoAdmin.Controllers;

[ApiController]
[Route("api/v1/[controller]")]
public class FinanceController : ControllerBase
{
    private readonly IMongoCollection<Transaction> _transactions;
    private readonly IMongoCollection<Player> _players;

    public FinanceController(IMongoDatabase database)
    {
        _transactions = database.GetCollection<Transaction>("transactions");
        _players = database.GetCollection<Player>("players");
    }

    [HttpGet("transactions")]
    public async Task<IEnumerable<Transaction>> GetTransactions([FromQuery] string? type)
    {
        var filter = Builders<Transaction>.Filter.Empty;
        if (!string.IsNullOrEmpty(type))
        {
            filter = Builders<Transaction>.Filter.Eq("Type", type);
        }
        return await _transactions.Find(filter).SortByDescending(t => t.CreatedAt).Limit(100).ToListAsync();
    }

    [HttpPost("transactions/{id}/approve")]
    public async Task<IActionResult> Approve(string id)
    {
        var tx = await _transactions.Find(t => t.Id == id).FirstOrDefaultAsync();
        if (tx == null) return NotFound("Transaction not found");

        var update = Builders<Transaction>.Update
            .Set(t => t.Status, "completed");
            
        await _transactions.UpdateOneAsync(t => t.Id == id, update);

        if (tx.Type == "deposit")
        {
            var balUpdate = Builders<Player>.Update.Inc(p => p.BalanceReal, tx.Amount);
            await _players.UpdateOneAsync(p => p.Id == tx.PlayerId, balUpdate);
        }

        return Ok(new { message = "Approved" });
    }
}
