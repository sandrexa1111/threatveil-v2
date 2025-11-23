import { LoadingSpinner } from '@/components/LoadingSpinner';

export default function Loading() {
  return (
    <div className="flex min-h-[300px] items-center justify-center">
      <LoadingSpinner />
    </div>
  );
}
