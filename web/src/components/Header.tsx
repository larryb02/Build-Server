import Box from '@mui/material/Box';

export default function Header() {
    return (
        <Box
            sx={{
                px: 3,
                py: 3,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'flex-end',
                borderBottom: '1px solid',
                borderColor: 'divider',
                flexShrink: 0,
            }}
        >
        </Box>
    );
}
