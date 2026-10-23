export function createTransferReference(amount: string, secret: string, prefix?: string): Promise<string>;
export function verifyTransferReference(reference: string, amount: string, secret: string, prefix?: string): Promise<boolean>;
