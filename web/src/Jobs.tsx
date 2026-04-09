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
import config from './config';

type Job = {
    job_id: number,
    git_repository_url: string,
    commit_hash: string,
    job_status: string,
}

type ChipColor = 'success' | 'error' | 'warning' | 'default';

function statusChip(status: string) {
    const map: Record<string, { color: ChipColor; label: string }> = {
        success:  { color: 'success', label: 'Success' },
        failed:   { color: 'error',   label: 'Failed' },
        running:  { color: 'warning', label: 'Running' },
    };
    const s = map[status.toLowerCase()] ?? { color: 'default', label: status };
    return <Chip label={s.label} color={s.color} size="small" />;
}

export default function Jobs() {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [error, setError] = useState(false);

    useEffect(() => {
        const fetchJobs = async () => {
            try {
                const res = await fetch(config.routes.jobs);
                if (!res.ok) {
                    throw new Error(`req responded with ${res.status} ${res.statusText}`);
                }
                const json = await res.json();
                console.log(json)
                setJobs(json);
            } catch (err) {
                console.error(`${err}`);
                setError(true);
            }
        }
        fetchJobs();
    }, [])

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <Typography variant="h5" sx={{ mb: 2 }}>Jobs</Typography>
            {error && <Alert severity="error" sx={{ mb: 2 }}>Something went wrong — could not load jobs.</Alert>}
            <TableContainer component={Paper} sx={{ flexGrow: 1, overflow: 'auto' }}>
                <Table stickyHeader>
                    <TableHead>
                        <TableRow>
                            <TableCell>Repository</TableCell>
                            <TableCell>Commit</TableCell>
                            <TableCell>Status</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {jobs.map((row) => (
                            <TableRow
                                key={row.job_id}
                                sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                            >
                                <TableCell>{row.git_repository_url}</TableCell>
                                <TableCell sx={{ fontFamily: 'monospace' }}>
                                    {row.commit_hash.slice(0, 7)}
                                </TableCell>
                                <TableCell>{statusChip(row.job_status)}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </Box>
    );
}
