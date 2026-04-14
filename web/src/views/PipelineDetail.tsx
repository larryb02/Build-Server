import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Chip from '@mui/material/Chip';
import Breadcrumbs from '@mui/material/Breadcrumbs';
import Link from '@mui/material/Link';

import { useEffect, useState } from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom';
import config from '../config';

type PipelineJob = {
    pipeline_job_id: number;
    name: string;
    status: string;
    created_at: string;
};

type PipelineDetail = {
    pipeline_id: number;
    project_id: number;
    project_name: string;
    branch: string;
    commit_hash: string;
    status: string;
    created_at: string;
    jobs: PipelineJob[];
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

export default function PipelineDetail() {
    const { id } = useParams<{ id: string }>();
    const [pipeline, setPipeline] = useState<PipelineDetail | null>(null);
    const [error, setError] = useState(false);

    useEffect(() => {
        const fetchDetail = async () => {
            try {
                const res = await fetch(`${config.routes.pipelines}/${id}`);
                if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
                setPipeline(await res.json());
            } catch (err) {
                console.error(`${err}`);
                setError(true);
            }
        };
        fetchDetail();
    }, [id]);

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <Breadcrumbs sx={{ mb: 2 }}>
                <Link component={RouterLink} to="/pipelines" underline="hover" color="inherit">
                    Pipelines
                </Link>
                <Typography color="text.primary">
                    {pipeline ? `${pipeline.branch} @ ${pipeline.commit_hash.slice(0, 7)}` : '…'}
                </Typography>
            </Breadcrumbs>

            {error && <Alert severity="error" sx={{ mb: 2 }}>Could not load pipeline.</Alert>}

            {pipeline && (
                <>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                        <Box sx={{ flexGrow: 1 }}>
                            <Typography variant="h5">
                                {pipeline.branch}
                                <Typography component="span" variant="h5" color="text.secondary" sx={{ fontFamily: 'monospace', ml: 1 }}>
                                    {pipeline.commit_hash.slice(0, 7)}
                                </Typography>
                            </Typography>
                            <Typography variant="body2" color="text.secondary">{pipeline.project_name}</Typography>
                        </Box>
                        {statusChip(pipeline.status)}
                    </Box>

                    <TableContainer component={Paper}>
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell>Job</TableCell>
                                    <TableCell>Status</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {pipeline.jobs.map((job) => (
                                    <TableRow
                                        key={job.pipeline_job_id}
                                        sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                                    >
                                        <TableCell sx={{ fontFamily: 'monospace' }}>{job.name}</TableCell>
                                        <TableCell>{statusChip(job.status)}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </>
            )}
        </Box>
    );
}
