import { z } from 'zod';

export const scanRequestSchema = z.object({
  domain: z
    .string()
    .trim()
    .toLowerCase()
    .regex(/^[a-z0-9.-]+\.[a-z]{2,}$/i, 'Provide a valid domain'),
  github_org: z
    .string()
    .trim()
    .regex(/^[a-z0-9-]+$/i, 'Org can only contain letters, numbers, and hyphens')
    .optional()
    .or(z.literal('')),
});

export type ScanRequestSchema = z.infer<typeof scanRequestSchema>;
