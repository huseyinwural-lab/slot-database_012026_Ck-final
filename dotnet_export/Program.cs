using MongoDB.Driver;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// MongoDB Config
var mongoUrl = builder.Configuration.GetValue<string>("MongoUrl") ?? "mongodb://localhost:27017";
var dbName = builder.Configuration.GetValue<string>("DbName") ?? "casino_admin_db";
var client = new MongoClient(mongoUrl);
var database = client.GetDatabase(dbName);
builder.Services.AddSingleton(database);

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseCors(x => x.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader());

app.UseAuthorization();

app.MapControllers();

app.Run();
