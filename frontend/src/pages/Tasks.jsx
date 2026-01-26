import React, { useEffect, useState } from 'react';
import { taskService } from '../services/taskService';
import { CheckCircle, Clock, AlertCircle } from 'lucide-react';
import clsx from 'clsx';
import { Link } from 'react-router-dom';

export default function Tasks() {
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('all'); // all, pending, completed

    useEffect(() => {
        fetchTasks();
    }, [filter]);

    const fetchTasks = async () => {
        setLoading(true);
        try {
            // If filter is 'all', pass null to service to get everything
            const statusFilter = filter === 'all' ? null : filter;
            const data = await taskService.getAll(0, 100, statusFilter);
            setTasks(data);
        } catch (error) {
            console.error("Failed to fetch tasks", error);
        } finally {
            setLoading(false);
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'completed': return 'bg-green-100 text-green-800 border-green-200';
            case 'in_progress': return 'bg-blue-100 text-blue-800 border-blue-200';
            case 'pending': return 'bg-orange-100 text-orange-800 border-orange-200';
            default: return 'bg-gray-100 text-gray-800 border-gray-200';
        }
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'completed': return <CheckCircle size={16} />;
            case 'in_progress': return <Clock size={16} />;
            default: return <AlertCircle size={16} />;
        }
    };

    return (
        <div className="flex flex-col h-full bg-gray-50">
            {/* Header */}
            <div className="p-4 bg-white border-b border-gray-200 sticky top-0 z-10">
                <h1 className="text-2xl font-bold text-gray-900 mb-4">My Tasks</h1>

                {/* Filter Tabs */}
                <div className="flex p-1 bg-gray-100 rounded-lg">
                    {['all', 'pending', 'completed'].map((f) => (
                        <button
                            key={f}
                            onClick={() => setFilter(f)}
                            className={clsx(
                                "flex-1 py-2 text-sm font-medium rounded-md capitalize transition-all",
                                filter === f ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
                            )}
                        >
                            {f}
                        </button>
                    ))}
                </div>
            </div>

            {/* Task List */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {loading ? (
                    <div className="flex justify-center p-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    </div>
                ) : tasks.length === 0 ? (
                    <div className="text-center py-10 text-gray-500">
                        <p>No tasks found.</p>
                    </div>
                ) : (
                    tasks.map((task) => (
                        <Link to={`/tasks/${task.id}`} key={task.id} className="block bg-white p-4 rounded-xl shadow-sm border border-gray-100 active:scale-[0.98] transition-transform">
                            <div className="flex justify-between items-start mb-2">
                                <span className={clsx(
                                    "px-2.5 py-0.5 rounded-full text-xs font-medium border flex items-center gap-1.5",
                                    getStatusColor(task.status)
                                )}>
                                    {getStatusIcon(task.status)}
                                    <span className="capitalize">{task.status.replace('_', ' ')}</span>
                                </span>
                                <span className="text-xs text-gray-400">
                                    #{task.id}
                                </span>
                            </div>

                            <h3 className="font-semibold text-gray-900 text-lg mb-1 line-clamp-1">{task.title}</h3>
                            <p className="text-gray-500 text-sm line-clamp-2 mb-3">
                                {task.description || "No description"}
                            </p>

                            <div className="text-xs text-gray-400 border-t pt-2 border-dashed">
                                Updated: {new Date(task.updated_at || task.created_at).toLocaleDateString()}
                            </div>
                        </Link>
                    ))
                )}
            </div>
        </div>
    );
}
