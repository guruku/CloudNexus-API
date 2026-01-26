import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { taskService } from '../services/taskService';
import { ArrowLeft, Calendar, CheckCircle, Clock, AlertCircle, Trash2 } from 'lucide-react';
import clsx from 'clsx';

export default function TaskDetail() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [task, setTask] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchTask();
    }, [id]);

    const fetchTask = async () => {
        try {
            const data = await taskService.getById(id);
            setTask(data);
        } catch (error) {
            console.error("Failed to fetch task", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="p-8 text-center">Loading...</div>;
    if (!task) return <div className="p-8 text-center">Task not found</div>;

    return (
        <div className="flex flex-col h-full bg-white relative">
            {/* Header */}
            <div className="absolute top-0 left-0 right-0 p-4 flex items-center bg-transparent z-10">
                <button
                    onClick={() => navigate(-1)}
                    className="p-2 bg-white/80 backdrop-blur-md shadow-sm rounded-full text-gray-700"
                >
                    <ArrowLeft size={20} />
                </button>
            </div>

            {/* Cover / Status Header */}
            <div className={clsx(
                "h-48 flex items-end p-6",
                task.status === 'completed' ? 'bg-green-100' :
                    task.status === 'in_progress' ? 'bg-blue-100' : 'bg-orange-100'
            )}>
                <div className="mb-2">
                    <span className={clsx(
                        "px-3 py-1 rounded-full text-sm font-semibold flex items-center gap-2 w-fit mb-2",
                        task.status === 'completed' ? 'bg-green-200 text-green-800' :
                            task.status === 'in_progress' ? 'bg-blue-200 text-blue-800' : 'bg-orange-200 text-orange-800'
                    )}>
                        {task.status === 'completed' ? <CheckCircle size={16} /> :
                            task.status === 'in_progress' ? <Clock size={16} /> : <AlertCircle size={16} />}
                        {task.status.replace('_', ' ').toUpperCase()}
                    </span>
                    <h1 className="text-2xl font-bold text-gray-900 leading-tight">
                        {task.title}
                    </h1>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 p-6 space-y-6 overflow-y-auto">

                {/* Date Info */}
                <div className="flex items-center gap-3 text-gray-500 text-sm">
                    <Calendar size={18} />
                    <span>Created: {new Date(task.created_at).toLocaleDateString()}</span>
                </div>

                {/* Description */}
                <div className="space-y-2">
                    <h3 className="font-semibold text-gray-900">Description</h3>
                    <p className="text-gray-600 whitespace-pre-wrap leading-relaxed">
                        {task.description || "No description provided."}
                    </p>
                </div>
            </div>

            {/* Actions */}
            <div className="p-4 border-t border-gray-100 bg-white sticky bottom-0 flex gap-3">
                {/* Only show 'Complete' button if not completed */}
                {task.status !== 'completed' && (
                    <button
                        className="flex-1 bg-green-600 text-white font-semibold py-3 rounded-xl shadow-lg shadow-green-500/30 active:scale-[0.98] transition-transform"
                        onClick={() => {
                            // Mock update logic since backend might not have update endpoint exposed in 'taskService' clearly 
                            // but usually PUT /items/{id} or similar. 
                            // Based on API review, main.py only has GET, POST. It MISSES PUT/PATCH. 
                            // Wait, I saw main.py earlier. Let me verify if there is an update endpoint.
                            // Checking step 9 (main.py):
                            // @app.get("/items/{item_id}") ...
                            // It does NOT have PUT/PATCH /items/{item_id}.
                            // So we cannot update tasks yet! 
                            // I should invoke a fix for backend or just notify user.
                            // Let's assume for now we just display it.
                            alert("Update feature pending backend implementation.");
                        }}
                    >
                        Mark Complete
                    </button>
                )}
            </div>
        </div>
    );
}
