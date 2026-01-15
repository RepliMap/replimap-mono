import { sql, relations } from "drizzle-orm";
import { integer, sqliteTable, text, index, unique } from "drizzle-orm/sqlite-core";

// ==========================================
// 🔵 MKSAAS CORE TABLES (Frontend / Auth)
// Time Format: Integer (Unix Timestamp MS)
// ==========================================

export const user = sqliteTable("user", {
    id: text("id").primaryKey(),
    name: text("name").notNull(),
    email: text("email").notNull().unique(),
    normalizedEmail: text("normalized_email").unique(),
    emailVerified: integer("email_verified", { mode: "boolean" })
        .default(false)
        .notNull(),
    image: text("image"),
    createdAt: integer("created_at", { mode: "timestamp_ms" })
        .default(sql`(cast(unixepoch('subsecond') * 1000 as integer))`)
        .notNull(),
    updatedAt: integer("updated_at", { mode: "timestamp_ms" })
        .default(sql`(cast(unixepoch('subsecond') * 1000 as integer))`)
        .$onUpdate(() => /* @__PURE__ */ new Date())
        .notNull(),
    role: text("role"),
    banned: integer("banned", { mode: "boolean" }).default(false),
    banReason: text("ban_reason"),
    banExpires: integer("ban_expires", { mode: "timestamp_ms" }),
    customerId: text("customer_id"),
}, (table) => ({
    userIdIdx: index("user_id_idx").on(table.id),
    userCustomerIdIdx: index("user_customer_id_idx").on(table.customerId),
    userRoleIdx: index("user_role_idx").on(table.role),
}));

export const session = sqliteTable("session", {
    id: text("id").primaryKey(),
    expiresAt: integer("expires_at", { mode: "timestamp_ms" }).notNull(),
    token: text("token").notNull().unique(),
    createdAt: integer("created_at", { mode: "timestamp_ms" })
        .default(sql`(cast(unixepoch('subsecond') * 1000 as integer))`)
        .notNull(),
    updatedAt: integer("updated_at", { mode: "timestamp_ms" })
        .$onUpdate(() => /* @__PURE__ */ new Date())
        .notNull(),
    ipAddress: text("ip_address"),
    userAgent: text("user_agent"),
    userId: text("user_id")
        .notNull()
        .references(() => user.id, { onDelete: "cascade" }),
    impersonatedBy: text("impersonated_by"),
}, (table) => ({
    sessionTokenIdx: index("session_token_idx").on(table.token),
    sessionUserIdIdx: index("session_user_id_idx").on(table.userId),
}));

export const account = sqliteTable("account", {
    id: text("id").primaryKey(),
    accountId: text("account_id").notNull(),
    providerId: text("provider_id").notNull(),
    userId: text("user_id")
        .notNull()
        .references(() => user.id, { onDelete: "cascade" }),
    accessToken: text("access_token"),
    refreshToken: text("refresh_token"),
    idToken: text("id_token"),
    accessTokenExpiresAt: integer("access_token_expires_at", {
        mode: "timestamp_ms",
    }),
    refreshTokenExpiresAt: integer("refresh_token_expires_at", {
        mode: "timestamp_ms",
    }),
    scope: text("scope"),
    password: text("password"),
    createdAt: integer("created_at", { mode: "timestamp_ms" })
        .default(sql`(cast(unixepoch('subsecond') * 1000 as integer))`)
        .notNull(),
    updatedAt: integer("updated_at", { mode: "timestamp_ms" })
        .$onUpdate(() => /* @__PURE__ */ new Date())
        .notNull(),
}, (table) => ({
    accountUserIdIdx: index("account_user_id_idx").on(table.userId),
    accountAccountIdIdx: index("account_account_id_idx").on(table.accountId),
    accountProviderIdIdx: index("account_provider_id_idx").on(table.providerId),
}));

export const verification = sqliteTable("verification", {
    id: text("id").primaryKey(),
    identifier: text("identifier").notNull(),
    value: text("value").notNull(),
    expiresAt: integer("expires_at", { mode: "timestamp_ms" }).notNull(),
    createdAt: integer("created_at", { mode: "timestamp_ms" })
        .default(sql`(cast(unixepoch('subsecond') * 1000 as integer))`)
        .notNull(),
    updatedAt: integer("updated_at", { mode: "timestamp_ms" })
        .default(sql`(cast(unixepoch('subsecond') * 1000 as integer))`)
        .$onUpdate(() => /* @__PURE__ */ new Date())
        .notNull(),
});

export const payment = sqliteTable("payment", {
    id: text("id").primaryKey(),
    priceId: text("price_id").notNull(),
    type: text("type").notNull(),
    scene: text("scene"),
    interval: text("interval"),
    userId: text("user_id").notNull().references(() => user.id, { onDelete: "cascade" }),
    customerId: text("customer_id").notNull(),
    subscriptionId: text("subscription_id"),
    sessionId: text("session_id"),
    invoiceId: text("invoice_id").unique(),
    status: text("status").notNull(),
    paid: integer("paid", { mode: "boolean" }).notNull().default(false),
    periodStart: integer("period_start", { mode: "timestamp_ms" }),
    periodEnd: integer("period_end", { mode: "timestamp_ms" }),
    cancelAtPeriodEnd: integer("cancel_at_period_end", { mode: "boolean" }),
    trialStart: integer("trial_start", { mode: "timestamp_ms" }),
    trialEnd: integer("trial_end", { mode: "timestamp_ms" }),
    createdAt: integer("created_at", { mode: "timestamp_ms" })
        .default(sql`(cast(unixepoch('subsecond') * 1000 as integer))`)
        .notNull(),
    updatedAt: integer("updated_at", { mode: "timestamp_ms" })
        .default(sql`(cast(unixepoch('subsecond') * 1000 as integer))`)
        .$onUpdate(() => /* @__PURE__ */ new Date())
        .notNull(),
}, (table) => ({
    paymentTypeIdx: index("payment_type_idx").on(table.type),
    paymentSceneIdx: index("payment_scene_idx").on(table.scene),
    paymentPriceIdIdx: index("payment_price_id_idx").on(table.priceId),
    paymentUserIdIdx: index("payment_user_id_idx").on(table.userId),
    paymentCustomerIdIdx: index("payment_customer_id_idx").on(table.customerId),
    paymentStatusIdx: index("payment_status_idx").on(table.status),
    paymentPaidIdx: index("payment_paid_idx").on(table.paid),
    paymentSubscriptionIdIdx: index("payment_subscription_id_idx").on(table.subscriptionId),
    paymentSessionIdIdx: index("payment_session_id_idx").on(table.sessionId),
    paymentInvoiceIdIdx: index("payment_invoice_id_idx").on(table.invoiceId),
}));

export const userCredit = sqliteTable("user_credit", {
    id: text("id").primaryKey(),
    userId: text("user_id").notNull().references(() => user.id, { onDelete: "cascade" }),
    currentCredits: integer("current_credits").notNull().default(0),
    lastRefreshAt: integer("last_refresh_at", { mode: "timestamp_ms" }),
    createdAt: integer("created_at", { mode: "timestamp_ms" })
        .default(sql`(cast(unixepoch('subsecond') * 1000 as integer))`)
        .notNull(),
    updatedAt: integer("updated_at", { mode: "timestamp_ms" })
        .default(sql`(cast(unixepoch('subsecond') * 1000 as integer))`)
        .$onUpdate(() => /* @__PURE__ */ new Date())
        .notNull(),
}, (table) => ({
    userCreditUserIdIdx: index("user_credit_user_id_idx").on(table.userId),
}));

export const creditTransaction = sqliteTable("credit_transaction", {
    id: text("id").primaryKey(),
    userId: text("user_id").notNull().references(() => user.id, { onDelete: "cascade" }),
    type: text("type").notNull(),
    description: text("description"),
    amount: integer("amount").notNull(),
    remainingAmount: integer("remaining_amount"),
    paymentId: text("payment_id"),
    expirationDate: integer("expiration_date", { mode: "timestamp_ms" }),
    expirationDateProcessedAt: integer("expiration_date_processed_at", { mode: "timestamp_ms" }),
    createdAt: integer("created_at", { mode: "timestamp_ms" })
        .default(sql`(cast(unixepoch('subsecond') * 1000 as integer))`)
        .notNull(),
    updatedAt: integer("updated_at", { mode: "timestamp_ms" })
        .default(sql`(cast(unixepoch('subsecond') * 1000 as integer))`)
        .$onUpdate(() => /* @__PURE__ */ new Date())
        .notNull(),
}, (table) => ({
    creditTransactionUserIdIdx: index("credit_transaction_user_id_idx").on(table.userId),
    creditTransactionTypeIdx: index("credit_transaction_type_idx").on(table.type),
}));

// ==========================================
// 🟠 REPLIMAP BACKEND TABLES
// Time Format: Text (ISO 8601 String)
// Note: Preserves compatibility with existing Worker
// ==========================================

/**
 * Licenses - Core licensing for RepliMap CLI
 * userId references MkSaaS `user` table (unified auth)
 *
 * Supports both subscription-based and one-time (lifetime) purchases.
 * - Subscriptions: stripeSubscriptionId is set, planType is 'monthly' or 'annual'
 * - Lifetime: stripeSessionId is set, planType is 'lifetime', currentPeriodEnd is '2099-12-31T23:59:59.000Z'
 */
export const licenses = sqliteTable("licenses", {
    id: text("id").primaryKey(),
    userId: text("user_id")
        .notNull()
        .references(() => user.id, { onDelete: "cascade" }),
    licenseKey: text("license_key").unique().notNull(),

    // Plan information
    plan: text("plan", { enum: ["free", "solo", "pro", "team"] })
        .default("free")
        .notNull(),
    planType: text("plan_type", { enum: ["free", "monthly", "annual", "lifetime"] })
        .default("monthly")
        .notNull(),

    // Status
    status: text("status", { enum: ["active", "canceled", "expired", "past_due", "revoked"] })
        .default("active")
        .notNull(),

    // Stripe references
    stripeSubscriptionId: text("stripe_subscription_id").unique(),
    stripePriceId: text("stripe_price_id"),
    stripeSessionId: text("stripe_session_id").unique(),  // For lifetime idempotency

    // Validity period
    currentPeriodStart: text("current_period_start"),
    currentPeriodEnd: text("current_period_end"),  // '2099-12-31T23:59:59.000Z' for lifetime

    // Timestamps
    createdAt: text("created_at")
        .default(sql`(datetime('now'))`)
        .notNull(),
    updatedAt: text("updated_at")
        .default(sql`(datetime('now'))`)
        .notNull(),
    canceledAt: text("canceled_at"),
    revokedAt: text("revoked_at"),
    revokedReason: text("revoked_reason"),
}, (table) => ({
    licensesUserIdIdx: index("licenses_user_id_idx").on(table.userId),
    licensesLicenseKeyIdx: index("licenses_license_key_idx").on(table.licenseKey),
    licensesPlanIdx: index("licenses_plan_idx").on(table.plan),
    licensesPlanTypeIdx: index("licenses_plan_type_idx").on(table.planType),
    licensesStatusIdx: index("licenses_status_idx").on(table.status),
    licensesSessionIdIdx: index("licenses_session_id_idx").on(table.stripeSessionId),
}));

/**
 * License Machines - Track activated machines per license
 */
export const licenseMachines = sqliteTable("license_machines", {
    id: text("id").primaryKey(),
    licenseId: text("license_id")
        .notNull()
        .references(() => licenses.id, { onDelete: "cascade" }),
    machineId: text("machine_id").notNull(),
    machineName: text("machine_name"),
    isActive: integer("is_active", { mode: "boolean" }).default(true).notNull(),
    firstSeenAt: text("first_seen_at")
        .default(sql`(datetime('now'))`)
        .notNull(),
    lastSeenAt: text("last_seen_at")
        .default(sql`(datetime('now'))`)
        .notNull(),
}, (table) => ({
    licenseMachinesLicenseIdIdx: index("license_machines_license_id_idx").on(table.licenseId),
    licenseMachinesUnique: unique("license_machines_unique").on(table.licenseId, table.machineId),
}));

/**
 * Machine Changes - Audit log for machine swaps
 */
export const machineChanges = sqliteTable("machine_changes", {
    id: text("id").primaryKey(),
    licenseId: text("license_id")
        .notNull()
        .references(() => licenses.id, { onDelete: "cascade" }),
    oldMachineId: text("old_machine_id"),
    newMachineId: text("new_machine_id").notNull(),
    changedAt: text("changed_at")
        .default(sql`(datetime('now'))`)
        .notNull(),
}, (table) => ({
    machineChangesLicenseIdIdx: index("machine_changes_license_id_idx").on(table.licenseId),
}));

/**
 * Usage Logs - CLI action tracking
 */
export const usageLogs = sqliteTable("usage_logs", {
    id: text("id").primaryKey(),
    licenseId: text("license_id")
        .notNull()
        .references(() => licenses.id, { onDelete: "cascade" }),
    machineId: text("machine_id"),
    action: text("action", { enum: ["validate", "activate", "deactivate", "scan"] }).notNull(),
    resourcesCount: integer("resources_count").default(0),
    // Type-safe JSON: auto-parse on read, auto-stringify on write
    metadata: text("metadata", { mode: "json" }).$type<Record<string, unknown> | null>(),
    createdAt: text("created_at")
        .default(sql`(datetime('now'))`)
        .notNull(),
}, (table) => ({
    usageLogsLicenseIdIdx: index("usage_logs_license_id_idx").on(table.licenseId),
    usageLogsCreatedAtIdx: index("usage_logs_created_at_idx").on(table.createdAt),
    usageLogsActionIdx: index("usage_logs_action_idx").on(table.action),
}));

/**
 * Processed Events - Stripe webhook idempotency
 */
export const processedEvents = sqliteTable("processed_events", {
    eventId: text("event_id").primaryKey(),
    eventType: text("event_type").notNull(),
    processedAt: text("processed_at")
        .default(sql`(datetime('now'))`)
        .notNull(),
}, (table) => ({
    processedEventsEventTypeIdx: index("processed_events_event_type_idx").on(table.eventType),
}));

/**
 * Usage Idempotency - Prevent duplicate usage tracking
 */
export const usageIdempotency = sqliteTable("usage_idempotency", {
    idempotencyKey: text("idempotency_key").primaryKey(),
    licenseId: text("license_id")
        .notNull()
        .references(() => licenses.id, { onDelete: "cascade" }),
    createdAt: text("created_at")
        .default(sql`(datetime('now'))`)
        .notNull(),
}, (table) => ({
    usageIdempotencyLicenseIdIdx: index("usage_idempotency_license_id_idx").on(table.licenseId),
}));

/**
 * License AWS Accounts - Multi-account support per license
 */
export const licenseAwsAccounts = sqliteTable("license_aws_accounts", {
    id: text("id").primaryKey(),
    licenseId: text("license_id")
        .notNull()
        .references(() => licenses.id, { onDelete: "cascade" }),
    awsAccountId: text("aws_account_id").notNull(),
    accountAlias: text("account_alias"),
    isActive: integer("is_active", { mode: "boolean" }).default(true).notNull(),
    firstSeenAt: text("first_seen_at")
        .default(sql`(datetime('now'))`)
        .notNull(),
    lastSeenAt: text("last_seen_at")
        .default(sql`(datetime('now'))`)
        .notNull(),
}, (table) => ({
    licenseAwsAccountsLicenseIdIdx: index("license_aws_accounts_license_id_idx").on(table.licenseId),
    licenseAwsAccountsUnique: unique("license_aws_accounts_unique").on(table.licenseId, table.awsAccountId),
}));

/**
 * Usage Events - Detailed telemetry from CLI
 */
export const usageEvents = sqliteTable("usage_events", {
    id: text("id").primaryKey(),
    licenseId: text("license_id")
        .notNull()
        .references(() => licenses.id, { onDelete: "cascade" }),
    eventType: text("event_type").notNull(),
    region: text("region"),
    vpcId: text("vpc_id"),
    resourceCount: integer("resource_count").default(0),
    durationMs: integer("duration_ms"),
    // Type-safe JSON: auto-parse on read, auto-stringify on write
    metadata: text("metadata", { mode: "json" }).$type<Record<string, unknown> | null>(),
    originalEventType: text("original_event_type"),
    createdAt: text("created_at")
        .default(sql`(datetime('now'))`)
        .notNull(),
}, (table) => ({
    usageEventsLicenseIdIdx: index("usage_events_license_id_idx").on(table.licenseId),
    usageEventsCreatedAtIdx: index("usage_events_created_at_idx").on(table.createdAt),
    usageEventsEventTypeIdx: index("usage_events_event_type_idx").on(table.eventType),
}));

/**
 * Snapshots - Infrastructure snapshots created by RepliMap
 */
export const snapshots = sqliteTable("snapshots", {
    id: text("id").primaryKey(),
    licenseId: text("license_id")
        .notNull()
        .references(() => licenses.id, { onDelete: "cascade" }),
    name: text("name").notNull(),
    region: text("region").notNull(),
    vpcId: text("vpc_id"),
    resourceCount: integer("resource_count").default(0),
    profile: text("profile"),
    replimapVersion: text("replimap_version"),
    storageType: text("storage_type").default("local"),
    storagePath: text("storage_path"),
    createdAt: text("created_at")
        .default(sql`(datetime('now'))`)
        .notNull(),
}, (table) => ({
    snapshotsLicenseIdIdx: index("snapshots_license_id_idx").on(table.licenseId),
    snapshotsCreatedAtIdx: index("snapshots_created_at_idx").on(table.createdAt),
}));

/**
 * Remediations - SOC2/compliance remediation tracking
 */
export const remediations = sqliteTable("remediations", {
    id: text("id").primaryKey(),
    licenseId: text("license_id")
        .notNull()
        .references(() => licenses.id, { onDelete: "cascade" }),
    auditId: text("audit_id"),
    region: text("region").notNull(),
    totalFindings: integer("total_findings").default(0),
    totalFixable: integer("total_fixable").default(0),
    totalManual: integer("total_manual").default(0),
    filesGenerated: integer("files_generated").default(0),
    createdAt: text("created_at")
        .default(sql`(datetime('now'))`)
        .notNull(),
}, (table) => ({
    remediationsLicenseIdIdx: index("remediations_license_id_idx").on(table.licenseId),
}));

/**
 * Migrations Log - Backend schema migration tracking
 * Note: Separate from Drizzle's own migration tracking
 */
export const migrationsLog = sqliteTable("migrations_log", {
    id: integer("id").primaryKey({ autoIncrement: true }),
    migrationName: text("migration_name").unique().notNull(),
    executedAt: text("executed_at")
        .default(sql`(datetime('now'))`)
        .notNull(),
    notes: text("notes"),
});

/**
 * Usage Daily - Aggregated daily statistics
 */
export const usageDaily = sqliteTable("usage_daily", {
    id: text("id").primaryKey(),
    licenseId: text("license_id")
        .notNull()
        .references(() => licenses.id, { onDelete: "cascade" }),
    date: text("date").notNull(), // YYYY-MM-DD format
    eventType: text("event_type").notNull(),
    count: integer("count").default(1).notNull(),
    resourceCount: integer("resource_count").default(0),
    createdAt: text("created_at")
        .default(sql`(datetime('now'))`)
        .notNull(),
    updatedAt: text("updated_at")
        .default(sql`(datetime('now'))`)
        .notNull(),
}, (table) => ({
    usageDailyLicenseIdIdx: index("usage_daily_license_id_idx").on(table.licenseId),
    usageDailyDateIdx: index("usage_daily_date_idx").on(table.date),
    usageDailyUnique: unique("usage_daily_unique").on(table.licenseId, table.date, table.eventType),
}));

// ==========================================
// DRIZZLE RELATIONS (Optional but Recommended)
// Enables: db.query.licenses.findMany({ with: { user: true, machines: true } })
// ==========================================

export const userRelations = relations(user, ({ many }) => ({
    sessions: many(session),
    accounts: many(account),
    payments: many(payment),
    licenses: many(licenses),
}));

export const sessionRelations = relations(session, ({ one }) => ({
    user: one(user, { fields: [session.userId], references: [user.id] }),
}));

export const accountRelations = relations(account, ({ one }) => ({
    user: one(user, { fields: [account.userId], references: [user.id] }),
}));

export const paymentRelations = relations(payment, ({ one }) => ({
    user: one(user, { fields: [payment.userId], references: [user.id] }),
}));

export const licensesRelations = relations(licenses, ({ one, many }) => ({
    user: one(user, { fields: [licenses.userId], references: [user.id] }),
    machines: many(licenseMachines),
    awsAccounts: many(licenseAwsAccounts),
    usageLogs: many(usageLogs),
    usageEvents: many(usageEvents),
    snapshots: many(snapshots),
    remediations: many(remediations),
    usageDaily: many(usageDaily),
}));

export const licenseMachinesRelations = relations(licenseMachines, ({ one }) => ({
    license: one(licenses, { fields: [licenseMachines.licenseId], references: [licenses.id] }),
}));

export const licenseAwsAccountsRelations = relations(licenseAwsAccounts, ({ one }) => ({
    license: one(licenses, { fields: [licenseAwsAccounts.licenseId], references: [licenses.id] }),
}));

export const usageLogsRelations = relations(usageLogs, ({ one }) => ({
    license: one(licenses, { fields: [usageLogs.licenseId], references: [licenses.id] }),
}));

export const usageEventsRelations = relations(usageEvents, ({ one }) => ({
    license: one(licenses, { fields: [usageEvents.licenseId], references: [licenses.id] }),
}));

export const snapshotsRelations = relations(snapshots, ({ one }) => ({
    license: one(licenses, { fields: [snapshots.licenseId], references: [licenses.id] }),
}));

export const remediationsRelations = relations(remediations, ({ one }) => ({
    license: one(licenses, { fields: [remediations.licenseId], references: [licenses.id] }),
}));

export const usageDailyRelations = relations(usageDaily, ({ one }) => ({
    license: one(licenses, { fields: [usageDaily.licenseId], references: [licenses.id] }),
}));

// ==========================================
// TYPE EXPORTS - MkSaaS
// ==========================================
export type User = typeof user.$inferSelect;
export type NewUser = typeof user.$inferInsert;

export type Session = typeof session.$inferSelect;
export type NewSession = typeof session.$inferInsert;

export type Account = typeof account.$inferSelect;
export type NewAccount = typeof account.$inferInsert;

export type Verification = typeof verification.$inferSelect;
export type NewVerification = typeof verification.$inferInsert;

export type Payment = typeof payment.$inferSelect;
export type NewPayment = typeof payment.$inferInsert;

export type UserCredit = typeof userCredit.$inferSelect;
export type NewUserCredit = typeof userCredit.$inferInsert;

export type CreditTransaction = typeof creditTransaction.$inferSelect;
export type NewCreditTransaction = typeof creditTransaction.$inferInsert;

// ==========================================
// TYPE EXPORTS - RepliMap
// ==========================================
export type License = typeof licenses.$inferSelect;
export type NewLicense = typeof licenses.$inferInsert;

export type LicensePlan = License["plan"];
export type LicensePlanType = License["planType"];
export type LicenseStatus = License["status"];

export type LicenseMachine = typeof licenseMachines.$inferSelect;
export type NewLicenseMachine = typeof licenseMachines.$inferInsert;

export type MachineChange = typeof machineChanges.$inferSelect;
export type NewMachineChange = typeof machineChanges.$inferInsert;

export type UsageLog = typeof usageLogs.$inferSelect;
export type NewUsageLog = typeof usageLogs.$inferInsert;

export type UsageAction = UsageLog["action"];

export type ProcessedEvent = typeof processedEvents.$inferSelect;
export type NewProcessedEvent = typeof processedEvents.$inferInsert;

export type UsageIdempotency = typeof usageIdempotency.$inferSelect;
export type NewUsageIdempotency = typeof usageIdempotency.$inferInsert;

export type LicenseAwsAccount = typeof licenseAwsAccounts.$inferSelect;
export type NewLicenseAwsAccount = typeof licenseAwsAccounts.$inferInsert;

export type UsageEvent = typeof usageEvents.$inferSelect;
export type NewUsageEvent = typeof usageEvents.$inferInsert;

export type Snapshot = typeof snapshots.$inferSelect;
export type NewSnapshot = typeof snapshots.$inferInsert;

export type Remediation = typeof remediations.$inferSelect;
export type NewRemediation = typeof remediations.$inferInsert;

export type MigrationLog = typeof migrationsLog.$inferSelect;
export type NewMigrationLog = typeof migrationsLog.$inferInsert;

export type UsageDaily = typeof usageDaily.$inferSelect;
export type NewUsageDaily = typeof usageDaily.$inferInsert;
