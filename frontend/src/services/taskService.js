import api from './api';

export const taskService = {
    // Get all tasks (supports pagination & filtering)
    getAll: async (skip = 0, limit = 100, status = null) => {
        const params = { skip, limit };
        if (status) params.status = status;

        const response = await api.get('/items', { params });
        return response.data;
    },

    // Get specific task
    getById: async (id) => {
        const response = await api.get(`/items/${id}`);
        return response.data;
    },

    // Create new task
    create: async (taskData) => {
        const response = await api.post('/items', taskData);
        return response.data;
    },

    // Upload file (uses different content-type)
    uploadFile: async (file) => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await api.post('/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    // Trigger backup
    backup: async () => {
        const response = await api.post('/backup');
        return response.data;
    }
};
