# 🎰 Casino Admin Panel - Comprehensive User Guide

## 📋 Table of Contents

1. [Overview](#overview)
2. [Dashboard](#dashboard)
3. [Player Management](#player-management)
4. [Game Management](#game-management)
5. [Finance Management](#finance-management)
6. [Bonus Management](#bonus-management)
7. [Admin Users](#admin-users)
8. [Feature Flags & A/B Testing](#feature-flags)
9. [Simulation Lab](#simulation-lab)
10. [Settings Panel](#settings-panel)
11. [Risk & Fraud Management](#risk-fraud)
12. [Reports](#reports)

---

## Overview

Casino Admin Panel is an enterprise-level management platform designed for casino operators. Manage all casino operations from one place - from player management to game configuration, bonus systems to risk management.

### Key Features
- 🎮 **Comprehensive Game Management** - RTP settings, VIP tables, custom tables
- 👥 **Detailed Player Profiles** - KYC, balance, game history, logs
- 💰 **Finance Module** - Deposit/withdrawal management, reports
- 🎁 **Advanced Bonus System** - Templates, rules, campaigns
- 🛡️ **Risk & Fraud Management** - AI-powered fraud detection
- 🧪 **Simulation Lab** - Game math and revenue simulations
- 🏢 **Multi-Tenant** - Multi-brand management

### System Requirements
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Minimum 1920x1080 resolution recommended
- Internet connection

---

## Dashboard

### Overview
Dashboard shows real-time status of your casino operations.

### Main KPIs
1. **GGR (Gross Gaming Revenue)** - Total gaming revenue
2. **NGR (Net Gaming Revenue)** - Net gaming revenue
3. **Active Players** - Number of active players
4. **Deposit Count** - Total deposits
5. **Withdrawal Count** - Total withdrawals

### Charts
- **Revenue Trend** - Last 7 days revenue trend
- **Player Activity** - Player activity graph
- **Top Games** - Most played games
- **Payment Status** - Payment statuses

### Usage
1. Select "Dashboard" from left menu
2. Use date picker to change date range
3. Click on any KPI card for detailed report
4. Use "Refresh" button to update data

---

## Player Management

### Player List

#### Filtering
Filter players by:
1. **Search Bar** - Search by email, username, or player ID
2. **Status Filter** - Active, Suspended, Blocked
3. **VIP Level** - Filter by VIP level
4. **Registration Date** - Filter by registration date

#### Sorting
- Player ID
- Username
- Registration Date
- Total Deposits
- Last Login

#### Bulk Operations
- **Bulk Suspend** - Suspend selected players
- **Bulk Export** - Export to Excel/CSV
- **Send Bulk Message** - Send message to selected players

### Player Detail Page

#### Tabs

**1. Profile**
- Basic information (Name, email, phone)
- VIP level
- Registration date
- Last login
- Status (Active/Suspended/Blocked)

**Actions:**
- ✏️ Edit Profile
- 🚫 Suspend Player
- ⛔ Block Player
- 📧 Send Email

**2. KYC (Identity Verification)**
- KYC level (Tier 1, 2, 3)
- Uploaded documents
- Verification status
- Verification notes

**Actions:**
- ✅ Approve Document
- ❌ Reject Document
- 📤 Request Additional Documents

**3. Balance**
- Real Money Balance
- Bonus Balance
- Locked Balance
- Total Wagering
- Pending Withdrawals

**Actions:**
- ➕ Manual Credit
- ➖ Manual Debit
- 🔒 Lock Balance
- 📊 View Transaction History

**4. Game History**
- List of played games
- Bet amounts
- Win/Loss status
- RTP realizations
- Last 100 sessions

**Filtering:**
- Date range
- Game type
- Provider
- Win/Loss

**5. Transaction Log**
- All financial transactions
- Deposits
- Withdrawals
- Bonuses
- Manual adjustments

**6. Activity Log**
- Login/logout records
- IP addresses
- Device information
- Suspicious activities

---

## Game Management

### Game List

#### General Settings
For each game:
- **Status** - Active/Inactive
- **RTP** - Return to Player percentage
- **Min/Max Bet** - Minimum and maximum bet limits
- **Volatility** - Game volatility
- **Hit Frequency** - Win frequency

#### RTP Management

**RTP Profiles:**
1. Standard (96.5%)
2. High (97.5%)
3. VIP (98%)
4. Custom

**Changing RTP:**
```
1. Select game
2. Click "Edit Game"
3. Go to "RTP Configuration" tab
4. Enter new RTP value
5. "Save Draft" -> Sent to Approval Queue
6. Active after Super Admin approval
```

⚠️ **Important:** RTP changes go through dual-control system.

### VIP & Custom Tables

#### Creating VIP Table
```
1. "Game Management" -> "VIP Games" tab
2. Click "Create VIP Table"
3. Fill form:
   - Table Name
   - Base Game ID
   - Min Bet (e.g., $100)
   - Max Bet (e.g., $10,000)
   - VIP Level Requirement (e.g., Level 3)
   - Max Players
   - Special Features (optional)
4. Click "Create"
```

**VIP Table Features:**
- High bet limits
- Custom RTP profiles
- Private room option
- Dedicated dealer (for live games)
- Special bonuses

### Paytable Management

Symbol weights and paytable configuration for slot games:

```
1. Select game
2. Click "Paytable Config"
3. For each symbol:
   - Reel weights (weight for each reel)
   - Payout values
   - Scatter/Wild configuration
4. "Save & Validate" - Automatic RTP calculation
5. "Submit for Approval"
```

### Jackpot Configuration

**Jackpot Types:**
1. **Fixed Jackpot** - Fixed jackpot
2. **Progressive Jackpot** - Progressive jackpot
3. **Multi-Level Jackpot** - Mini, Minor, Major, Grand

**Settings:**
- Seed Amount - Starting amount
- Contribution % - Percentage from each bet to jackpot
- Win Probability - Win probability
- Max Cap - Maximum limit

---

## Finance Management

### Deposit Management

#### Deposit Requests
View pending deposit requests:

**Columns:**
- Player ID/Username
- Amount
- Payment Method
- Status (Pending, Approved, Rejected)
- Request Time
- Processing Time

**Actions:**
1. **Approve** - Approve deposit
   - Automatically added to player balance
   - Transaction log created
   - Email sent to player

2. **Reject** - Reject deposit
   - Select rejection reason
   - Notification sent to player

3. **Flag as Suspicious** - Flag as suspicious
   - Sent to risk engine
   - Requires manual review

### Withdrawal Management

#### Withdrawal Requests

**Approval Process:**
```
1. Check Pending Withdrawals list
2. Review player profile
3. Check KYC status
4. Review recent activity
5. Check fraud check results
6. Approve or Reject
```

**Automatic Checks:**
- ✅ KYC Level check
- ✅ Wagering requirement met?
- ✅ Duplicate withdrawal check
- ✅ Velocity check
- ✅ Device fingerprint match
- ✅ IP location match

**Rejection Reasons:**
- KYC not completed
- Wagering not met
- Suspicious activity
- Document verification required
- Duplicate account suspected

### Financial Reports

#### Report Types

**1. Daily Revenue Report**
- GGR/NGR breakdown
- By game provider
- By game category
- By player segment

**2. Deposit/Withdrawal Report**
- Success rates
- Average amounts
- By payment method
- Processing times

**3. Bonus Cost Report**
- Total bonus issued
- Bonus used
- Wagering completed
- ROI analysis

**Export Options:**
- 📄 PDF
- 📊 Excel
- 📋 CSV
- 📧 Email Schedule (daily/weekly)

---

## Bonus Management

### Bonus Templates

#### Bonus Types

**1. Welcome Bonus**
```yaml
Example Configuration:
- Type: Deposit Match
- Percentage: 100%
- Max Amount: $500
- Wagering: 35x
- Min Deposit: $20
- Valid Days: 30
- Eligible Games: All Slots
- Max Bet: $5
```

**2. Reload Bonus**
- For existing players
- Weekly/Monthly
- Lower percentages (25-50%)

**3. Cashback**
- Loss-based cashback
- Percentage: 5-20%
- Weekly/Monthly
- No wagering or low wagering

**4. Free Spins**
- Specific games
- Spin value
- Wagering on winnings
- Expiry period

**5. VIP Reload**
- VIP level based
- Higher limits
- Lower wagering
- Priority processing

### Bonus Rules

#### Wagering Requirements
```
Example Calculation:
Bonus Amount: $100
Wagering: 35x
Total Wagering Required: $100 x 35 = $3,500

Game Contributions:
- Slots: 100%
- Table Games: 10%
- Live Casino: 10%
- Video Poker: 5%
```

#### Maximum Bet
Maximum bet limit while bonus active (e.g., $5)

#### Game Restrictions
Certain games cannot be played with bonus

#### Validity Period
Validity period after bonus activation (e.g., 30 days)

### Creating Campaign

**Step by Step:**
```
1. Bonus Management -> "Create Campaign"
2. Campaign Details:
   - Name: "Weekend Reload 50%"
   - Type: Reload Bonus
   - Start Date: Friday 00:00
   - End Date: Sunday 23:59

3. Bonus Configuration:
   - Percentage: 50%
   - Max Bonus: $200
   - Wagering: 30x
   - Min Deposit: $25

4. Target Audience:
   - All Active Players
   - or
   - Specific Segment (VIP, Inactive, etc.)
   - Country: All or selected countries

5. Communication:
   - ✅ Email notification
   - ✅ SMS notification
   - ✅ In-app notification
   - Bonus Code: WEEKEND50 (optional)

6. Preview & Submit
```

---

## Admin Users

### Admin User Management

#### Roles and Permissions

**Admin Roles:**
1. **Super Admin** - Full access to everything
2. **Manager** - Access to most modules
3. **Support** - Read-only access
4. **Finance Team** - Deposit/withdrawal approval
5. **Fraud Analyst** - Risk & fraud module

### Admin Activity Log

**Tracked Actions:**
- Player limit changes
- Manual bonus loading
- Game RTP changes
- Fraud freeze/unfreeze
- Config changes
- Withdrawal approvals
- CMS content updates

**Log Columns:**
- Admin ID + Name
- Action
- Module
- Before / After snapshot
- IP Address
- Timestamp
- Risk Level

**Usage:**
```
1. Admin Management -> "Activity Log" tab
2. Filter:
   - Select admin
   - Select module (Players, Finance, Games, etc.)
   - Select action type
   - Date range
3. "View Diff" - View changes
4. "Export Log" - CSV export
```

### Permission Matrix

Visualizes role-based permissions.

**Permission Types:**
- Read - View
- Write - Edit
- Approve - Approve
- Export - Data export
- Restricted - Sensitive data access

### IP & Device Restrictions

**IP Restrictions:**
```
Allowed IP (Whitelist):
1. IP & Device tab -> "Add IP"
2. IP Address: 192.168.1.0/24
3. Type: Allowed
4. Reason: "Office network"
5. Submit

Blocked IP (Blacklist):
1. Suspicious IP detected
2. Type: Blocked
3. Reason: "Suspicious login attempts"
```

**Device Management:**
- When admin logs in from new device
- Device goes to "Pending" status
- Super Admin approval required
- Access restricted until approved

### Login History

**Displayed Information:**
- Admin name
- Login time
- IP address
- Device information
- Location
- Result (Success/Failed)
- Failure reason

**Suspicious Login Detection:**
- ⚠️ New device
- ⚠️ New country
- ⚠️ Multiple failed attempts
- ⚠️ Unusual hours

---

## Feature Flags

### What is Feature Flag?

Feature flags allow you to test new features on specific user groups before full release.

### Creating Flag

```
1. Feature Flags -> "Create Flag"
2. Flag Configuration:
   - Flag ID: new_payment_flow
   - Name: New Payment Flow
   - Description: New payment flow
   - Type: Boolean
   - Default Value: false
   - Scope: Frontend
   - Environment: Production
   - Group: Payments

3. Targeting:
   - Rollout %: 10% (10% of traffic)
   - Countries: TR, DE (only these countries)
   - VIP Levels: 3, 4, 5 (VIPs only)
   - Device: mobile/web

4. Create Flag
```

### Flag Management

**Toggle On/Off:**
```
1. Select flag from list
2. Use toggle button to on/off
3. Recorded in audit log
```

**Edit Targeting:**
```
1. Click on flag
2. "Edit Targeting"
3. Change rollout %
4. Update country list
5. Save
```

**Analytics:**
```
1. Select flag
2. "View Analytics"
3. KPIs:
   - Activation Rate: 87.5%
   - Conversion Impact: +12.3%
   - Error Rate: 0.02%
   - Users Exposed: 45K
```

### A/B Testing

**Creating Experiment:**
```
1. Experiments tab
2. "Create Experiment"

Step 1 - General Info:
- Name: "Deposit Button Color Test"
- Description: "Green vs Blue button"
- Feature Flag: new_deposit_button (optional)

Step 2 - Variants:
- Variant A (Control): 50% - Blue button
- Variant B: 50% - Green button

Step 3 - Targeting:
- Countries: TR
- New users only: Yes
- VIP: All

Step 4 - Metrics:
- Primary: Conversion Rate
- Secondary: Click-through Rate, Deposit Amount
- Min Sample Size: 5,000

5. Start Experiment
```

### Kill Switch

⚠️ **EMERGENCY BUTTON**

Turns off all feature flags with one click.

```
Usage:
1. Red "Kill Switch" button at top right
2. Confirmation: "Are you sure you want to disable all flags?"
3. Yes - All flags go to OFF status
4. Recorded in audit log
```

**When to Use:**
- Critical bug in production
- System performance issue
- Security breach
- Urgent rollback needed

---

## Simulation Lab

### Game Math Simulator

Simulate game math to test RTP, volatility, and win distribution.

#### Slots Simulator

**Usage:**
```
1. Simulation Lab -> "Game Math" tab
2. Slots Simulator

Configuration:
- Game: Select Big Win Slots
- Spins: 10,000 (Quick test)
  or 1,000,000 (Production test)
- RTP Override: 96.5%
- Seed: Empty (random) or specific seed

3. Click "Run Simulation"
4. Wait (10K spins ~5 seconds)
```

**Results:**
```
Summary Metrics:
- Total Spins: 10,000
- Total Bet: $10,000
- Total Win: $9,652
- Simulated RTP: 96.52%
- Volatility Index: 7.2
- Hit Frequency: 32.5%
- Bonus Hit Frequency: 3.2%
- Max Single Win: $125,000

Win Distribution:
- 0x (No win): 4,500 spins (45%)
- 0-1x: 3,200 spins (32%)
- 1-10x: 1,800 spins (18%)
- 10-50x: 400 spins (4%)
- 50-100x: 80 spins (0.8%)
- 100x+: 20 spins (0.2%)
```

**Export:**
- 📊 Show Graphs - Visual charts
- 📄 Export CSV - First 10,000 spins
- 📁 Download Bundle (ZIP) - All config + results

---

## Settings Panel

### Brand Management

Brand management for multi-brand operations.

**Adding New Brand:**
```
1. Settings -> Brands tab
2. "Add Brand" button

Form:
- Brand Name: Super777
- Default Currency: EUR
- Default Language: en
- Domains: super777.com, www.super777.com
- Languages Supported: en, es, pt
- Logo Upload: (select file)
- Favicon Upload: (select file)
- Contact Info:
  - Support Email: support@super777.com
  - Support Phone: +1-555-0123
- Timezone: UTC+1
- Country Availability: ES, PT, BR

3. "Create" button
```

### Currency Management

Currencies and exchange rates.

**Displayed Information:**
- Currency Code (USD, EUR, TRY, GBP)
- Symbol ($, €, ₺, £)
- Exchange Rate (Base: USD = 1.0)
- Min/Max Deposit
- Min/Max Bet

**Updating Exchange Rates:**
```
1. Currencies tab
2. "Sync Rates" button
3. Current rates pulled from external API
4. Automatic update
```

### Country Rules

Country-based restrictions and rules.

**Columns:**
- Country Name & Code
- Allowed (Yes/No)
- Games Allowed
- Bonuses Allowed
- KYC Level (1, 2, 3)
- Payment Restrictions

### Platform Defaults

Global system defaults.

**Settings:**
```
- Default Language: en
- Default Currency: USD
- Default Timezone: UTC
- Session Timeout: 30 minutes
- Password Min Length: 8 characters
- Require 2FA: No (optional)
- Cache TTL: 300 seconds
- Pagination: 20 items per page
- API Rate Limit: 60 requests/minute
```

### API Key Management

API keys and webhook management.

**Creating API Key:**
```
1. API Keys tab
2. "Generate Key"

Form:
- Key Name: Production API
- Owner: Brand/System
- Permissions:
  - ✅ Read
  - ✅ Write
  - ⬜ Delete
  - ✅ Admin

3. Generate

Response:
API Key: sk_live_abc123xyz456... (SHOWN ONCE)
Key ID: key_789

⚠️ Save the API key in a secure location!
```

---

## Best Practices

### Security
1. ✅ Enable 2FA for all admins
2. ✅ Use IP whitelist
3. ✅ Rotate API keys regularly
4. ✅ Mask sensitive data in logs
5. ✅ Regular security audits

### Operational
1. ✅ Review daily reports
2. ✅ Check withdrawal queue 2-3 times daily
3. ✅ Resolve risk cases within 24 hours
4. ✅ Respond to player complaints quickly
5. ✅ Take regular backups

### Testing
1. ✅ Test new games in Simulation Lab
2. ✅ Simulate RTP changes
3. ✅ Start feature flags at 10%
4. ✅ A/B tests minimum 5K sample size
5. ✅ Monitor bonus ROI continuously

### Compliance
1. ✅ Keep KYC verifications up to date
2. ✅ Review AML thresholds regularly
3. ✅ Follow license requirements
4. ✅ Promote RG tools to players
5. ✅ Preserve audit logs

---

## Keyboard Shortcuts

- `Ctrl+K` - Global search
- `Ctrl+/` - Command palette
- `Ctrl+R` - Refresh data
- `Ctrl+E` - Export current view
- `Esc` - Close modal/dialog

---

## Version Information

**Version:** 2.0.0
**Last Updated:** December 2024
**Platform:** FastAPI + React + MongoDB

---

**💡 Tip:** This guide is regularly updated. Check `/docs` for the latest version.
