# Casino Admin Panel - Comprehensive User Manual

This document is a comprehensive guide detailing all modules and features of the Casino Management Panel.

## Table of Contents
1. [Introduction and Overview](#1-introduction-and-overview)
2. [Dashboard](#2-dashboard)
3. [Player Management](#3-player-management)
4. [Finance Management](#4-finance-management)
5. [Game Management](#5-game-management)
6. [Bonus and Campaigns](#6-bonus-and-campaigns)
7. [Risk and Fraud Management](#7-risk-and-fraud-management)
8. [CRM and Communication](#8-crm-and-communication)
9. [Content Management (CMS)](#9-content-management-cms)
10. [Support Desk](#10-support-desk)
11. [Affiliate Management](#11-affiliate-management)
12. [Responsible Gaming (RG)](#12-responsible-gaming-rg)
13. [Admin and Security Management](#13-admin-and-security-management)
14. [Feature Flags and A/B Testing](#14-feature-flags-and-ab-testing)
15. [Simulation Lab](#15-simulation-lab)
16. [Settings Panel (Multi-Tenant)](#16-settings-panel-multi-tenant)

---

## 1. Introduction and Overview
This panel is a multi-tenant, modular structure designed to manage all aspects of a modern online casino operation.

**Key Features:**
*   **Role-Based Access:** Users can only see modules they are authorized for.
*   **Multi-Tenant:** Multiple brands can be managed from a single panel.
*   **Real-Time Data:** Dashboards and reports are powered by instant data.

---

## 2. Dashboard
The main screen encountered after login. It shows the general health of the operation.
*   **KPI Cards:** Daily Deposit, Withdrawal, GGR (Gross Gaming Revenue), NGR (Net Gaming Revenue), Active Player count.
*   **Charts:** Hourly/Daily revenue trends.
*   **Live Feed:** Last registered players, last big wins, last deposits.
*   **Emergencies:** Pending risky withdrawals or high-amount transactions awaiting approval.

---

## 3. Player Management
The section where the entire lifecycle of players is managed.
*   **Player List:** Player search with advanced filtering (ID, Email, Username, IP, Registration Date).
*   **Player Profile:**
    *   **General:** Balance, loyalty points, VIP level.
    *   **Wallet:** Real money and bonus balance details.
    *   **Game History:** Games played, bet/win details.
    *   **Transaction History:** All deposits and withdrawals.
    *   **KYC:** Identity verification documents and statuses.
    *   **Notes:** Customer representative notes.

---

## 4. Finance Management
The center where money inflows and outflows are controlled.
*   **Deposit Requests:** Pending, approved, and rejected deposits. Action buttons for methods requiring manual approval.
*   **Withdrawal Requests:** Player withdrawal requests. High risk score transactions automatically fall into "Review" status.
*   **Reports:** Reports based on payment providers, daily cash report.

---

## 5. Game Management
The area where the casino lobby is managed.
*   **Game List:** All games, providers, RTP rates.
*   **Game Editing:** Editing game name, category, images, and active status.
*   **Category Management:** Editing lobby categories like "Popular", "New", "Slots".

---

## 6. Bonus and Campaigns
The module where player incentives are managed.
*   **Bonus Definitions:** Creating Welcome, Deposit, Loss (Cashback) bonuses.
*   **Rules:** Wagering requirements, maximum win, eligible games.
*   **Tournaments:** Creating tournaments with leaderboards.

---

## 7. Risk and Fraud Management
The security center where suspicious activities are detected.
*   **Rules:** Defining rules like "More than 5 accounts from same IP", "Rapid consecutive withdrawal attempts".
*   **Case Management:** Interface where suspicious players marked by the system are reviewed.
*   **Blacklist:** Banned IP, Email, or Device lists.

---

## 8. CRM and Communication
The module for communicating with players.
*   **Segmentation:** Creating dynamic groups like "Inactive for last 30 days", "VIP users".
*   **Campaigns:** Creating and scheduling Email, SMS, or Push notification campaigns.
*   **Templates:** Managing ready-made message templates.

---

## 9. Content Management (CMS)
The area where website content is managed.
*   **Pages:** Editing static pages like "About Us", "FAQ", "Rules".
*   **Banners:** Managing home page sliders and promotion images.
*   **Announcements:** In-site ticker or pop-up announcements.

---

## 10. Support Desk
The area where customer complaints and requests are managed.
*   **Tickets:** Requests coming via email or form.
*   **Live Support:** (If integrated) Live chat logs.
*   **Canned Responses:** Quick response templates for frequently asked questions.

---

## 11. Affiliate Management
Management of partners providing traffic.
*   **Affiliate List:** Partner accounts and approval processes.
*   **Commission Plans:** CPA, RevShare (Revenue Share), or Hybrid models.
*   **Reports:** Which partner brought how much traffic and players, earnings.

---

## 12. Responsible Gaming (RG)
Legal compliance and player protection module.
*   **Limits:** Tracking deposit/loss limits set by players themselves.
*   **Self-Exclusion:** Players who have closed their accounts temporarily/permanently.
*   **Alerts:** Automatic alerts for players exhibiting risky gaming behavior.

---

## 13. Admin and Security Management (NEW)
Advanced module controlling panel security and admin access.
*   **Admin Users:** Creating, editing, and freezing admin accounts.
*   **Roles and Permissions:** Defining roles like "Finance Team", "Support Team".
*   **Audit Log:** Detailed log showing which admin performed what action when (with before/after values).
*   **Permission Matrix:** Viewing and editing permissions (Read/Write/Approve/Export) of all roles in all modules on a single screen.
*   **IP and Device Restrictions:**
    *   **IP Whitelist:** Allowing admin login only from specific IPs.
    *   **Device Approval:** Requiring admin approval when logging in from a new device.
*   **Login History:** All successful and failed admin login attempts.

---

## 14. Feature Flags and A/B Testing (NEW)
Technical module where software features and experiments are managed.
*   **Feature Flags:** Turning a new feature (e.g., New Payment Page) on/off without code changes or enabling it only for a specific audience (e.g., Beta users).
*   **A/B Testing (Experiments)::** Testing different versions of a feature (Variant A vs Variant B) and measuring which one is more successful (Conversion rate, Revenue, etc.).
*   **Segments:** Defining target audiences for flags (e.g., "iOS users in Turkey").
*   **Kill Switch:** Ability to turn off all new features with a single button in emergencies.

---

## 15. Simulation Lab (NEW)
Advanced simulation tool used to test the impact of operational decisions beforehand.
*   **Game Math:** Verifying real RTP, Volatility, and Maximum Win values by simulating a slot game 1 million times.
*   **Bonus Simulator:** Testing the profitability of a bonus campaign. (e.g., If we give 100% bonus, how much will the house lose/win?)
*   **Portfolio Simulator:** Estimating the effect of changing games' positions in the lobby or RTP rates on general turnover.
*   **Risk Scenarios:** Testing how many innocent users (False Positives) a new fraud rule will affect.

---

## 16. Settings Panel (Multi-Tenant) (NEW)
Multi-brand management center where general system configuration is done.
*   **Brands:** Creating a new casino brand (Tenant), setting domain and language.
*   **Currencies:** Managing valid currencies and exchange rates in the system.
*   **Country Rules (Geoblocking)::** Determining which countries to accept players from, which games are banned in which country.
*   **API Keys:** Generating secure API keys for external system integrations.
*   **Platform Defaults:** System-wide settings like session timeouts, default language.

---
*This document is prepared based on the December 2025 development period.*
