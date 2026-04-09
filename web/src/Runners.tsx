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

import { useEffect, useState } from 'react';
import config from './config';

type Runner = {
    runner_id: number,
    name: string,
    health: string,
}

type ChipColor = 'success' | 'error' | 'warning' | 'default';

function healthChip(health: string) {
    const map: Record<string, { color: ChipColor; label: string }> = {
        healthy:   { color: 'success', label: 'Healthy' },
        unhealthy: { color: 'error',   label: 'Unhealthy' },
        unknown:   { color: 'warning', label: 'Unknown' },
    };
    const h = map[health.toLowerCase()] ?? { color: 'default', label: health };
    return <Chip label={h.label} color={h.color} size="small" />;
}

export default function Runners() {
    const [runners, setRunners] = useState<Runner[]>([]);
    const [error, setError] = useState(false);

    useEffect(() => {
        const fetchRunners = async () => {
            try {
                const res = await fetch(config.routes.runners);
                if (!res.ok) {
                    throw new Error(`req responded with ${res.status} ${res.statusText}`);
                }
                const json = await res.json();
                console.log(json)
                setRunners(json);
            } catch (err) {
                console.error(`${err}`);
                setError(true);
            }
        }
        fetchRunners();
    }, [])

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <Typography variant="h5" sx={{ mb: 2 }}>Runners</Typography>
            {error && <Alert severity="error" sx={{ mb: 2 }}>Something went wrong — could not load runners.</Alert>}
            <TableContainer component={Paper} sx={{ flexGrow: 1, overflow: 'auto' }}>
                <Table stickyHeader>
                    <TableHead>
                        <TableRow>
                            <TableCell>Name</TableCell>
                            <TableCell>Health</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {runners.map((row) => (
                            <TableRow
                                key={row.runner_id}
                                sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                            >
                                <TableCell>{row.name}</TableCell>
                                {/* <TableCell>{healthChip(row.health)}</TableCell> */}
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </Box>
    );
}
