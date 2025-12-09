using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

namespace CasinoAdmin.Models;

public enum PlayerStatus { Active, Suspended, Banned, SelfExcluded }
public enum KYCStatus { Pending, Approved, Rejected, NotSubmitted }

public class Player
{
    [BsonId]
    [BsonRepresentation(BsonType.ObjectId)]
    public string? Id { get; set; }
    
    public string TenantId { get; set; } = "default_casino";
    public string Username { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public string? Phone { get; set; }
    public decimal BalanceReal { get; set; }
    public decimal BalanceBonus { get; set; }
    
    [BsonRepresentation(BsonType.String)]
    public PlayerStatus Status { get; set; } = PlayerStatus.Active;
    
    public int VipLevel { get; set; } = 1;
    
    [BsonRepresentation(BsonType.String)]
    public KYCStatus KycStatus { get; set; } = KYCStatus.NotSubmitted;
    
    public DateTime RegisteredAt { get; set; } = DateTime.UtcNow;
    public DateTime? LastLogin { get; set; }
    public string Country { get; set; } = "Unknown";
    public string RiskScore { get; set; } = "low";
}

public class Transaction
{
    [BsonId]
    [BsonRepresentation(BsonType.ObjectId)]
    public string? Id { get; set; }
    public string PlayerId { get; set; } = string.Empty;
    public string Type { get; set; } = "deposit"; // deposit, withdrawal
    public decimal Amount { get; set; }
    public string Status { get; set; } = "pending";
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}

public class FeatureFlag
{
    [BsonId]
    [BsonRepresentation(BsonType.ObjectId)]
    public string? Id { get; set; }
    public string Key { get; set; } = string.Empty;
    public bool IsEnabled { get; set; }
    public string Description { get; set; } = string.Empty;
}
