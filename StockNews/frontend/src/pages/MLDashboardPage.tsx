/** ML Model Dashboard page. */

import { useMarket } from '../contexts/MarketContext';
import { useMLDashboard } from '../hooks/useMLDashboard';
import ModelCard from '../components/ml/ModelCard';
import TierStatus from '../components/ml/TierStatus';
import AccuracyTrendChart from '../components/ml/AccuracyTrendChart';
import FeatureImportanceChart from '../components/ml/FeatureImportanceChart';
import ConfusionMatrix from '../components/ml/ConfusionMatrix';
import DirectionAccuracy from '../components/ml/DirectionAccuracy';

export default function MLDashboardPage() {
  const { market } = useMarket();
  const {
    stats,
    models,
    activeModel,
    isLoading,
    trainModel,
    isTraining,
    activateModel,
    evaluateModel,
    isEvaluating,
    evaluateResult,
  } = useMLDashboard(market);

  const currentSamples = stats?.markets.find(m => m.market === market)?.labeled_records ?? 0;

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">ML Model Dashboard</h1>
        <div className="flex gap-2">
          <button
            onClick={() => trainModel({ market, modelType: 'lightgbm', featureTier: 1 })}
            disabled={isTraining}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {isTraining ? 'Training...' : 'Train New Model'}
          </button>
          <button
            onClick={() => evaluateModel(market)}
            disabled={isEvaluating || !activeModel}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            {isEvaluating ? 'Evaluating...' : 'Evaluate'}
          </button>
        </div>
      </div>

      {/* Top row: Model Card + Accuracy Trend */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6">
          <ModelCard model={activeModel} />
          <TierStatus currentSamples={currentSamples} activeTier={activeModel?.feature_tier ?? null} />
        </div>
        <div className="lg:col-span-2 space-y-6">
          <AccuracyTrendChart models={models} />
          <FeatureImportanceChart importances={activeModel?.feature_importances ?? null} />
        </div>
      </div>

      {/* Bottom row: Confusion Matrix + Direction Accuracy */}
      {evaluateResult && evaluateResult.status === 'evaluated' && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <ConfusionMatrix
            matrix={evaluateResult.confusion_matrix ?? null}
            labels={evaluateResult.labels ?? null}
          />
          <DirectionAccuracy
            precision={evaluateResult.precision ?? null}
            recall={evaluateResult.recall ?? null}
            f1={evaluateResult.f1 ?? null}
          />
        </div>
      )}

      {/* Model list */}
      {models.length > 0 && (
        <div className="rounded-lg border bg-white shadow-sm">
          <div className="border-b p-4">
            <h3 className="text-sm font-semibold text-gray-500">All Models</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-xs text-gray-500">
                <tr>
                  <th className="p-3">Name</th>
                  <th className="p-3">Type</th>
                  <th className="p-3">Tier</th>
                  <th className="p-3">CV Acc</th>
                  <th className="p-3">Samples</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {models.map(m => (
                  <tr key={m.id} className="hover:bg-gray-50">
                    <td className="p-3 font-medium">{m.model_name}</td>
                    <td className="p-3">{m.model_type}</td>
                    <td className="p-3">T{m.feature_tier}</td>
                    <td className="p-3">{m.cv_accuracy != null ? `${(m.cv_accuracy * 100).toFixed(1)}%` : '-'}</td>
                    <td className="p-3">{m.train_samples?.toLocaleString() ?? '-'}</td>
                    <td className="p-3">
                      {m.is_active ? (
                        <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700">Active</span>
                      ) : (
                        <span className="text-xs text-gray-400">Inactive</span>
                      )}
                    </td>
                    <td className="p-3">
                      {!m.is_active && (
                        <button
                          onClick={() => activateModel(m.id)}
                          className="text-xs text-blue-600 hover:underline"
                        >
                          Activate
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
