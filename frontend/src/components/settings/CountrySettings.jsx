import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';

const CountrySettings = ({ countryRules }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">Country Rules & Geoblocking</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Country</TableHead>
              <TableHead>Allowed</TableHead>
              <TableHead>Games</TableHead>
              <TableHead>Bonuses</TableHead>
              <TableHead>KYC Level</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {countryRules.map(rule => (
              <TableRow key={rule.id}>
                <TableCell className="font-medium">{rule.country_name} ({rule.country_code})</TableCell>
                <TableCell><Badge variant={rule.is_allowed ? 'default' : 'destructive'}>{rule.is_allowed ? 'Yes' : 'No'}</Badge></TableCell>
                <TableCell>{rule.games_allowed ? '✓' : '✗'}</TableCell>
                <TableCell>{rule.bonuses_allowed ? '✓' : '✗'}</TableCell>
                <TableCell><Badge variant="outline">Level {rule.kyc_level}</Badge></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
};

export default CountrySettings;
