import authConfig from '../../../fixtures/bank-transfer-auth.json';
import {
  createTransferReference as signReference,
  verifyTransferReference as verifyReference,
} from '../../shared/transferReference.mjs';

export function createTransferReference(amount: string): Promise<string> {
  return signReference(amount, authConfig.sharedKey, authConfig.payloadPrefix);
}

export function verifyTransferReference(reference: string, amount: string): Promise<boolean> {
  return verifyReference(reference, amount, authConfig.sharedKey, authConfig.payloadPrefix);
}
