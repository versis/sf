import { copyTextToClipboard } from './clipboardUtils';

interface ShareData {
  title?: string;
  text?: string;
  url?: string;
}

interface ShareOrCopyOptions {
  onShareSuccess?: (message: string) => void;
  onCopySuccess?: (message: string) => void;
  onShareError?: (message: string) => void;
  onCopyError?: (message: string) => void;
  shareSuccessMessage?: string;
  copySuccessMessage?: string;
  shareErrorMessage?: string;
  copyErrorMessage?: string;
}

export async function shareOrCopy(
  shareData: ShareData,
  fallbackTextToCopy: string,
  options?: ShareOrCopyOptions
): Promise<void> {
  let copied = false;
  try {
    if (navigator.share) {
      await navigator.share(shareData);
      if (options?.onShareSuccess) {
        options.onShareSuccess(options.shareSuccessMessage || 'Shared successfully!');
      }
      // Some might want to copy even if share succeeds, but typically not.
      // For now, if share succeeds, we don't attempt to copy.
    } else {
      // navigator.share not available, fall back to copying.
      copied = await copyTextToClipboard(fallbackTextToCopy, {
        onSuccess: options?.onCopySuccess,
        onError: options?.onCopyError,
        successMessage: options?.copySuccessMessage,
        errorMessage: options?.copyErrorMessage,
      });
      if (!copied && options?.onCopyError && !navigator.clipboard) {
        // If copyTextToClipboard returned false due to no clipboard API,
        // and an onCopyError callback exists, it would have been called by copyTextToClipboard.
        // We can re-iterate or trust copyTextToClipboard handled it.
      } else if (!copied && options?.onCopyError) {
        // General copy failure not related to clipboard API availability.
        // options.onCopyError(options.copyErrorMessage || 'Failed to copy fallback text.');
        // This would be redundant as copyTextToClipboard should have called it.
      }
    }
  } catch (err) {
    console.error('Share failed, attempting to copy fallback text:', err);
    if (options?.onShareError) {
        options.onShareError(options.shareErrorMessage || 'Sharing failed. Attempting to copy link.');
    }
    // Attempt to copy fallback text if share operation itself throws an error.
    if (!copied) { // Check if we haven't already tried and reported copy status
        await copyTextToClipboard(fallbackTextToCopy, {
            onSuccess: options?.onCopySuccess,
            onError: options?.onCopyError,
            successMessage: options?.copySuccessMessage,
            errorMessage: options?.copyErrorMessage,
        });
    }
  }
} 