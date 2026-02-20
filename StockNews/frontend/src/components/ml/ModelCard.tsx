/** Active model summary card. */

import type { MLModel } from '../../types/training';

interface Props {
  model: MLModel | null;
}

export default function ModelCard({ model }: Props) {
  if (!model) {
    return (
      <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-6 text-center">
        <p className="text-sm text-gray-500">No active model</p>
        <p className="mt-1 text-xs text-gray-400">Train and activate a model to see details</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-white p-6 shadow-sm">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-500">Active Model</h3>
        <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">Active</span>
      </div>
      <p className="text-lg font-bold text-gray-900">{model.model_type === 'lightgbm' ? 'LightGBM' : 'Random Forest'}</p>
      <div className="mt-3 space-y-1 text-sm text-gray-600">
        <p>Tier {model.feature_tier} &middot; {model.feature_list.length} features</p>
        <p>Market: {model.market}</p>
        {model.cv_accuracy != null && (
          <p className="text-lg font-semibold text-blue-600">{(model.cv_accuracy * 100).toFixed(1)}% CV accuracy</p>
        )}
        {model.cv_std != null && (
          <p className="text-xs text-gray-400">&plusmn; {(model.cv_std * 100).toFixed(1)}%</p>
        )}
        <p className="text-xs text-gray-400">{model.train_samples?.toLocaleString()} training samples</p>
      </div>
    </div>
  );
}
