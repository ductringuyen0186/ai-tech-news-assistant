export default function Settings() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">Configure your AI Tech News Assistant</p>
      </div>

      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Coming Soon</h2>
        <p className="text-gray-600">
          Settings panel will include configuration for:
        </p>
        <ul className="mt-4 space-y-2 text-sm text-gray-600">
          <li>• RSS feed sources</li>
          <li>• AI model preferences</li>
          <li>• Summarization settings</li>
          <li>• Search preferences</li>
          <li>• Notification settings</li>
        </ul>
      </div>
    </div>
  )
}
