import { Dialog } from '@headlessui/react';

/**
 * Modal displaying user achievements.
 * Currently a placeholder with static content.
 */
export default function AchievementModal({ isOpen, onClose }) {
  return (
    <Dialog open={isOpen} onClose={onClose} className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50" aria-hidden="true" />
      <Dialog.Panel className="z-10 w-full max-w-md rounded-lg bg-white p-6 text-gray-800">
        <Dialog.Title className="text-lg font-bold mb-4">Achievements</Dialog.Title>
        <p className="mb-4">No achievements yet.</p>
        <button
          className="mt-2 rounded-md bg-blue-600 px-4 py-2 text-white"
          onClick={onClose}
        >
          Close
        </button>
      </Dialog.Panel>
    </Dialog>
  );
}
