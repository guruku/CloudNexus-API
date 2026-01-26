import React, { useState } from 'react';
import { taskService } from '../services/taskService';
import { useNavigate } from 'react-router-dom';
import { Save, Upload, X } from 'lucide-react';
import clsx from 'clsx';

export default function CreateTask() {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        status: 'pending'
    });
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            let finalDescription = formData.description;

            // Handle file upload if exists
            if (file) {
                try {
                    const uploadRes = await taskService.uploadFile(file);
                    // Append file URL to description since we don't have a file field in DB yet
                    finalDescription += `\n\nAttachment: ${uploadRes.s3_url}`;
                } catch (err) {
                    console.error("Upload failed", err);
                    // Continue creating task but warn user? For now just log.
                }
            }

            await taskService.create({
                ...formData,
                description: finalDescription
            });

            navigate('/tasks');
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to create task');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleFileChange = (e) => {
        if (e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    return (
        <div className="flex flex-col h-full bg-white">
            <div className="p-4 border-b border-gray-100 flex items-center justify-between sticky top-0 bg-white z-10">
                <h1 className="text-xl font-bold text-gray-900">New Task</h1>
                <button
                    onClick={() => navigate(-1)}
                    className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
                >
                    <X size={24} />
                </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-6 flex-1 overflow-y-auto">
                {error && (
                    <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg">
                        {error}
                    </div>
                )}

                <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-700">Title</label>
                    <input
                        type="text"
                        required
                        className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all outline-none"
                        placeholder="What needs to be done?"
                        value={formData.title}
                        onChange={e => setFormData({ ...formData, title: e.target.value })}
                    />
                </div>

                <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-700">Description</label>
                    <textarea
                        className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all outline-none min-h-[120px] resize-y"
                        placeholder="Add details..."
                        value={formData.description}
                        onChange={e => setFormData({ ...formData, description: e.target.value })}
                    />
                </div>

                <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-700">Status</label>
                    <div className="grid grid-cols-3 gap-3">
                        {['pending', 'in_progress', 'completed'].map(status => (
                            <button
                                key={status}
                                type="button"
                                onClick={() => setFormData({ ...formData, status })}
                                className={clsx(
                                    "py-2 px-3 rounded-lg text-sm font-medium border capitalize transition-all",
                                    formData.status === status
                                        ? "bg-blue-50 border-blue-200 text-blue-700 ring-1 ring-blue-500/20"
                                        : "bg-white border-gray-200 text-gray-600 hover:bg-gray-50"
                                )}
                            >
                                {status.replace('_', ' ')}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-700">Attachment</label>
                    <div className="border-2 border-dashed border-gray-200 rounded-xl p-4 text-center hover:bg-gray-50 transition-colors cursor-pointer relative">
                        <input
                            type="file"
                            onChange={handleFileChange}
                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        />
                        <div className="flex flex-col items-center gap-2 text-gray-400">
                            <Upload size={24} />
                            <span className="text-xs">
                                {file ? file.name : "Tap to upload file"}
                            </span>
                        </div>
                    </div>
                </div>
            </form>

            <div className="p-4 border-t border-gray-100 bg-white sticky bottom-0">
                <button
                    onClick={handleSubmit}
                    disabled={loading}
                    className="w-full bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-semibold py-3.5 rounded-xl shadow-lg shadow-blue-500/30 flex items-center justify-center gap-2 transition-all disabled:opacity-70 disabled:cursor-not-allowed"
                >
                    {loading ? (
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                        <>
                            <Save size={20} />
                            <span>Save Task</span>
                        </>
                    )}
                </button>
            </div>
        </div>
    );
}
