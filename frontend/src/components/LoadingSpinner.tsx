interface LoadingSpinnerProps {
  size?: 'sm' | 'md';
}

const sizeMap = {
  sm: 'h-4 w-4',
  md: 'h-8 w-8',
};

export function LoadingSpinner({ size = 'md' }: LoadingSpinnerProps) {
  return <span className={`inline-block animate-spin rounded-full border-2 border-slate-300 border-t-cyan-400 ${sizeMap[size]}`} />;
}
