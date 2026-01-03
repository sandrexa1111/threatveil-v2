'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';

export default function SettingsPage() {
    return (
        <div className="space-y-8">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
                <p className="text-muted-foreground">
                    Manage your account settings and preferences.
                </p>
            </div>

            <div className="grid gap-8">
                <Card>
                    <CardHeader>
                        <CardTitle>Account</CardTitle>
                        <CardDescription>
                            Update your account information.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-2">
                            <Label htmlFor="email">Email</Label>
                            <Input id="email" defaultValue="demo@threatveil.com" disabled />
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="name">Name</Label>
                            <Input id="name" defaultValue="Demo User" />
                        </div>
                        <Button>Save Changes</Button>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Notifications</CardTitle>
                        <CardDescription>
                            Configure how you receive alerts.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center justify-between space-x-2">
                            <Label htmlFor="email-alerts" className="flex flex-col space-y-1">
                                <span>Email Alerts</span>
                                <span className="font-normal text-muted-foreground">Receive emails about new high-risk findings.</span>
                            </Label>
                            <Switch id="email-alerts" defaultChecked />
                        </div>
                        <div className="flex items-center justify-between space-x-2">
                            <Label htmlFor="marketing-emails" className="flex flex-col space-y-1">
                                <span>Marketing Emails</span>
                                <span className="font-normal text-muted-foreground">Receive product updates and offers.</span>
                            </Label>
                            <Switch id="marketing-emails" />
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Billing</CardTitle>
                        <CardDescription>
                            Manage your subscription and payment methods.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="rounded-md border border-dashed p-8 text-center">
                            <p className="text-muted-foreground">Stripe integration coming soon.</p>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
