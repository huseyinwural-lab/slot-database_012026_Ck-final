using CasinoAdmin.Models;
using Microsoft.AspNetCore.Mvc;
using MongoDB.Driver;

namespace CasinoAdmin.Controllers;

[ApiController]
[Route("api/v1/[controller]")]
public class PlayersController : ControllerBase
{
    private readonly IMongoCollection<Player> _players;

    public PlayersController(IMongoDatabase database)
    {
        _players = database.GetCollection<Player>("players");
    }

    [HttpGet]
    public async Task<IEnumerable<Player>> Get([FromQuery] string? status)
    {
        var filter = Builders<Player>.Filter.Empty;
        if (!string.IsNullOrEmpty(status))
        {
            filter = Builders<Player>.Filter.Eq("Status", status);
        }
        return await _players.Find(filter).Limit(100).ToListAsync();
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<Player>> GetById(string id)
    {
        var player = await _players.Find(p => p.Id == id).FirstOrDefaultAsync();
        if (player == null) return NotFound();
        return player;
    }

    [HttpPut("{id}")]
    public async Task<IActionResult> Update(string id, [FromBody] Player update)
    {
        var result = await _players.ReplaceOneAsync(p => p.Id == id, update);
        if (result.MatchedCount == 0) return NotFound();
        return Ok(new { message = "Player updated" });
    }
}
