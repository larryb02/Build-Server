import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Alert from '@mui/material/Alert';

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import config from '../config';

type Pipeline = {
    pipeline_id: number;
    project_id: number;
    name: string;
    branch: string;
    commit_hash: string;
    status: string;
    created_at: string;
};

type ChipColor = 'success' | 'error' | 'warning' | 'default';

function statusChip(status: string) {
    const map: Record<string, { color: ChipColor; label: string }> = {
        succeeded: { color: 'success', label: 'Succeeded' },
        failed:    { color: 'error',   label: 'Failed' },
        running:   { color: 'warning', label: 'Running' },
        queued:    { color: 'default', label: 'Queued' },
    };
    const s = map[status.toLowerCase()] ?? { color: 'default', label: status };
    return <Chip label={s.label} color={s.color} size="small" />;
}

export default function Pipelines() {
    const [pipelines, setPipelines] = useState<Pipeline[]>([]);
    const [error, setError] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchPipelines = async () => {
            try {
                const res = await fetch(config.routes.pipelines);
                if (!res.ok) {
                    throw new Error(`req responded with ${res.status} ${res.statusText}`);
                }
                const json = await res.json();
                setPipelines(json);
            } catch (err) {
                console.error(`${err}`);
                setError(true);
            }
        };
        fetchPipelines();
    }, []);

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <Typography variant="h5" sx={{ mb: 2 }}>Pipelines</Typography>
            {error && <Alert severity="error" sx={{ mb: 2 }}>Something went wrong — could not load pipelines.</Alert>}
            <TableContainer component={Paper} sx={{ flexGrow: 1, overflow: 'auto' }}>
                <Table stickyHeader>
                    <TableHead>
                        <TableRow>
                            <TableCell>Name</TableCell>
                            <TableCell>Commit</TableCell>
                            <TableCell>Status</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {pipelines.map((row) => (
                            <TableRow
                                key={row.pipeline_id}
                                hover
                                onClick={() => navigate(`/pipelines/${row.pipeline_id}`)}
                                sx={{ cursor: 'pointer', '&:last-child td, &:last-child th': { border: 0 } }}
                            >
                                <TableCell sx={{ color: 'text.disabled', fontStyle: 'italic' }}>--</TableCell>
                                <TableCell sx={{ fontFamily: 'monospace' }}>
                                    {row.commit_hash.slice(0, 7)}
                                </TableCell>
                                <TableCell>{statusChip(row.status)}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </Box>
    );
}
