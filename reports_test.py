import requests
import sys
import json
from datetime import datetime

class ReportsAPITester:
    def __init__(self, base_url="https://securepay-13.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            response = None
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    return True, response_data
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append({
                    "name": name,
                    "endpoint": endpoint,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response.text[:200]
                })
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                "name": name,
                "endpoint": endpoint,
                "error": str(e)
            })
            return False, {}

    def test_all_16_report_types(self):
        """Test ALL 16 Report Types - Comprehensive Testing"""
        print("\n📊 TESTING ALL 16 REPORT TYPES - COMPREHENSIVE")
        
        report_tests = []
        
        # 1. Overview Report - KPI data
        success1, overview_response = self.run_test("1. Overview Report - KPI Data", "GET", "api/v1/reports/overview", 200)
        if success1 and isinstance(overview_response, dict):
            required_fields = ['ggr', 'ngr', 'total_deposits', 'total_withdrawals', 'active_players', 'new_registrations', 'bonus_cost', 'fraud_loss']
            missing_fields = [field for field in required_fields if field not in overview_response]
            if not missing_fields:
                print("✅ Overview Report structure is complete")
                print(f"   💰 GGR: ${overview_response['ggr']:,.2f}")
                print(f"   💚 NGR: ${overview_response['ngr']:,.2f}")
                print(f"   👥 Active Players: {overview_response['active_players']}")
            else:
                print(f"⚠️  Overview Report missing fields: {missing_fields}")
        report_tests.append(success1)
        
        # 2. Financial Report
        success2, financial_response = self.run_test("2. Financial Report", "GET", "api/v1/reports/financial", 200)
        if success2 and isinstance(financial_response, list) and len(financial_response) > 0:
            financial_item = financial_response[0]
            required_fields = ['date', 'ggr', 'ngr', 'deposits', 'withdrawals']
            if all(field in financial_item for field in required_fields):
                print("✅ Financial Report structure is complete")
                print(f"   📅 Sample: {financial_item['date']} - GGR: ${financial_item['ggr']}")
            else:
                print(f"⚠️  Financial Report missing fields")
        report_tests.append(success2)
        
        # 3. Players Report (LTV)
        success3, players_response = self.run_test("3. Players Report (LTV)", "GET", "api/v1/reports/players/ltv", 200)
        if success3 and isinstance(players_response, list) and len(players_response) > 0:
            player_item = players_response[0]
            required_fields = ['player_id', 'deposits', 'withdrawals', 'net_revenue', 'vip']
            if all(field in player_item for field in required_fields):
                print("✅ Players Report structure is complete")
                print(f"   👤 Sample: {player_item['player_id']} - Net Revenue: ${player_item['net_revenue']}")
            else:
                print(f"⚠️  Players Report missing fields")
        report_tests.append(success3)
        
        # 4. Games Report
        success4, games_response = self.run_test("4. Games Report", "GET", "api/v1/reports/games", 200)
        if success4 and isinstance(games_response, list) and len(games_response) > 0:
            game_item = games_response[0]
            required_fields = ['game', 'provider', 'bets', 'wins', 'ggr']
            if all(field in game_item for field in required_fields):
                print("✅ Games Report structure is complete")
                print(f"   🎮 Sample: {game_item['game']} - GGR: ${game_item['ggr']}")
            else:
                print(f"⚠️  Games Report missing fields")
        report_tests.append(success4)
        
        # 5. Provider Report
        success5, provider_response = self.run_test("5. Provider Report", "GET", "api/v1/reports/providers", 200)
        if success5 and isinstance(provider_response, list) and len(provider_response) > 0:
            provider_item = provider_response[0]
            required_fields = ['provider', 'ggr', 'rtp', 'bet_count']
            if all(field in provider_item for field in required_fields):
                print("✅ Provider Report structure is complete")
                print(f"   🏢 Sample: {provider_item['provider']} - GGR: ${provider_item['ggr']}")
            else:
                print(f"⚠️  Provider Report missing fields")
        report_tests.append(success5)
        
        # 6. Bonus Report
        success6, bonus_response = self.run_test("6. Bonus Report", "GET", "api/v1/reports/bonuses", 200)
        if success6 and isinstance(bonus_response, list) and len(bonus_response) > 0:
            bonus_item = bonus_response[0]
            required_fields = ['type', 'cost', 'claimed', 'roi']
            if all(field in bonus_item for field in required_fields):
                print("✅ Bonus Report structure is complete")
                print(f"   🎁 Sample: {bonus_item['type']} - ROI: {bonus_item['roi']}%")
            else:
                print(f"⚠️  Bonus Report missing fields")
        report_tests.append(success6)
        
        # 7. Affiliate Report
        success7, affiliate_response = self.run_test("7. Affiliate Report", "GET", "api/v1/reports/affiliates", 200)
        if success7 and isinstance(affiliate_response, list) and len(affiliate_response) > 0:
            affiliate_item = affiliate_response[0]
            required_fields = ['affiliate', 'ftd', 'cpa_cost', 'revenue_share']
            if all(field in affiliate_item for field in required_fields):
                print("✅ Affiliate Report structure is complete")
                print(f"   🤝 Sample: {affiliate_item['affiliate']} - FTD: {affiliate_item['ftd']}")
            else:
                print(f"⚠️  Affiliate Report missing fields")
        report_tests.append(success7)
        
        # 8. Risk Report
        success8, risk_response = self.run_test("8. Risk Report", "GET", "api/v1/reports/risk", 200)
        if success8 and isinstance(risk_response, list) and len(risk_response) > 0:
            risk_item = risk_response[0]
            required_fields = ['metric', 'count', 'prevented_loss']
            if all(field in risk_item for field in required_fields):
                print("✅ Risk Report structure is complete")
                print(f"   🛡️ Sample: {risk_item['metric']} - Prevented Loss: ${risk_item['prevented_loss']}")
            else:
                print(f"⚠️  Risk Report missing fields")
        report_tests.append(success8)
        
        # 9. RG (Responsible Gaming) Report
        success9, rg_response = self.run_test("9. RG (Responsible Gaming) Report", "GET", "api/v1/reports/rg", 200)
        if success9 and isinstance(rg_response, list) and len(rg_response) > 0:
            rg_item = rg_response[0]
            required_fields = ['metric', 'count', 'trend']
            if all(field in rg_item for field in required_fields):
                print("✅ RG Report structure is complete")
                print(f"   ⚖️ Sample: {rg_item['metric']} - Count: {rg_item['count']}")
            else:
                print(f"⚠️  RG Report missing fields")
        report_tests.append(success9)
        
        # 10. KYC Report
        success10, kyc_response = self.run_test("10. KYC Report", "GET", "api/v1/reports/kyc", 200)
        if success10 and isinstance(kyc_response, list) and len(kyc_response) > 0:
            kyc_item = kyc_response[0]
            required_fields = ['status', 'count', 'avg_time']
            if all(field in kyc_item for field in required_fields):
                print("✅ KYC Report structure is complete")
                print(f"   📋 Sample: {kyc_item['status']} - Count: {kyc_item['count']}")
            else:
                print(f"⚠️  KYC Report missing fields")
        report_tests.append(success10)
        
        # 11. CRM Report
        success11, crm_response = self.run_test("11. CRM Report", "GET", "api/v1/reports/crm", 200)
        if success11 and isinstance(crm_response, list) and len(crm_response) > 0:
            crm_item = crm_response[0]
            required_fields = ['campaign', 'channel', 'sent', 'open_rate', 'conversion']
            if all(field in crm_item for field in required_fields):
                print("✅ CRM Report structure is complete")
                print(f"   📧 Sample: {crm_item['campaign']} - Open Rate: {crm_item['open_rate']}%")
            else:
                print(f"⚠️  CRM Report missing fields")
        report_tests.append(success11)
        
        # 12. CMS Report
        success12, cms_response = self.run_test("12. CMS Report", "GET", "api/v1/reports/cms", 200)
        if success12 and isinstance(cms_response, list) and len(cms_response) > 0:
            cms_item = cms_response[0]
            # CMS report has mixed structure, check for basic fields
            if 'page' in cms_item or 'banner' in cms_item:
                print("✅ CMS Report structure is complete")
                if 'page' in cms_item:
                    print(f"   🌐 Sample: {cms_item['page']} - Views: {cms_item.get('views', 'N/A')}")
                else:
                    print(f"   🖼️ Sample: {cms_item['banner']} - Impressions: {cms_item.get('impressions', 'N/A')}")
            else:
                print(f"⚠️  CMS Report missing expected fields")
        report_tests.append(success12)
        
        # 13. Operational Report
        success13, operational_response = self.run_test("13. Operational Report", "GET", "api/v1/reports/operational", 200)
        if success13 and isinstance(operational_response, list) and len(operational_response) > 0:
            operational_item = operational_response[0]
            required_fields = ['metric', 'value']
            if all(field in operational_item for field in required_fields):
                print("✅ Operational Report structure is complete")
                print(f"   ⚙️ Sample: {operational_item['metric']} - Value: {operational_item['value']}")
            else:
                print(f"⚠️  Operational Report missing fields")
        report_tests.append(success13)
        
        # 14. Scheduled Reports
        success14, scheduled_response = self.run_test("14. Scheduled Reports", "GET", "api/v1/reports/schedules", 200)
        if success14 and isinstance(scheduled_response, list):
            print("✅ Scheduled Reports endpoint accessible")
            print(f"   📅 Found {len(scheduled_response)} scheduled reports")
        report_tests.append(success14)
        
        # 15. Export Reports
        success15, export_response = self.run_test("15. Export Reports", "GET", "api/v1/reports/exports", 200)
        if success15 and isinstance(export_response, list):
            print("✅ Export Reports endpoint accessible")
            print(f"   📤 Found {len(export_response)} export jobs")
        report_tests.append(success15)
        
        # 16. Audit Report
        success16, audit_response = self.run_test("16. Audit Report", "GET", "api/v1/reports/audit", 200)
        if success16 and isinstance(audit_response, list):
            print("✅ Audit Report endpoint accessible")
            print(f"   📝 Found {len(audit_response)} audit entries")
        report_tests.append(success16)
        
        # Summary
        passed_reports = sum(report_tests)
        total_reports = len(report_tests)
        print(f"\n📊 REPORT TYPES SUMMARY: {passed_reports}/{total_reports} reports working")
        
        if passed_reports == total_reports:
            print("🎉 ALL 16 REPORT TYPES ARE FUNCTIONAL!")
        else:
            failed_reports = total_reports - passed_reports
            print(f"⚠️  {failed_reports} report types have issues")
            
        # Print failed tests details
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS DETAILS:")
            for failed in self.failed_tests:
                error_msg = failed.get('error', f'Status {failed.get("actual", "unknown")}')
                print(f"   - {failed['name']}: {error_msg}")
        
        return passed_reports, total_reports, self.failed_tests

def main():
    print("📊 Reports Module Testing - ALL 16 REPORT TYPES")
    print("=" * 60)
    
    tester = ReportsAPITester()
    
    # Test all 16 report types
    passed, total, failed_tests = tester.test_all_16_report_types()
    
    # Print final summary
    print("\n" + "=" * 60)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 SUCCESS: All 16 report types are functional!")
        return 0
    else:
        print(f"\n⚠️  WARNING: {total - passed} report types have issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())