interface CopyToClipboardOptions {
  onSuccess?: (message: string) => void;
  onError?: (message: string) => void;
  successMessage?: string;
  errorMessage?: string;
}

export async function copyTextToClipboard(
  textToCopy: string,
  options?: CopyToClipboardOptions
): Promise<boolean> {
  if (!navigator.clipboard) {
    if (options?.onError) {
      options.onError(options.errorMessage || 'Clipboard API not available.');
    }
    console.warn('Clipboard API not available.');
    return false;
  }

  try {
    await navigator.clipboard.writeText(textToCopy);
    if (options?.onSuccess) {
      options.onSuccess(options.successMessage || 'Copied to clipboard!');
    }
    return true;
  } catch (err) {
    console.error('Failed to copy text: ', err);
    if (options?.onError) {
      options.onError(options.errorMessage || 'Failed to copy.');
    }
    return false;
  }
} 