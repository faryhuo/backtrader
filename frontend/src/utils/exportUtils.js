/**
 * Export utilities for DataSource page
 * Handles CSV, Excel, and image exports
 */

import { message } from 'antd';

/**
 * Export data to CSV format
 * @param {Array} data - Array of data objects
 * @param {string} filename - Name of the file to download
 * @param {Object} tickerInfo - Ticker information object
 */
export const exportToCSV = (data, filename, tickerInfo = null) => {
    if (!data || data.length === 0) {
        console.warn('No data to export');
        return;
    }

    // Prepare CSV headers
    const headers = ['Date', 'Open', 'High', 'Low', 'Close'];
    if (data[0].volume !== undefined) {
        headers.push('Volume');
    }

    // Add ticker info as comments if available
    let csvContent = '';
    if (tickerInfo) {
        csvContent += `# Ticker: ${tickerInfo.ticker}\n`;
        csvContent += `# Name: ${tickerInfo.long_name || 'N/A'}\n`;
        csvContent += `# Export Date: ${new Date().toISOString()}\n`;
        csvContent += '#\n';
    }

    // Add headers
    csvContent += headers.join(',') + '\n';

    // Add data rows
    data.forEach(row => {
        const values = [
            row.time,
            row.open,
            row.high,
            row.low,
            row.close
        ];
        if (row.volume !== undefined) {
            values.push(row.volume);
        }
        csvContent += values.join(',') + '\n';
    });

    // Create and download file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    downloadBlob(blob, filename);
};

/**
 * Export data to Excel format (requires xlsx library)
 * @param {Array} data - Array of data objects
 * @param {string} filename - Name of the file to download
 * @param {Object} tickerInfo - Ticker information object
 */
export const exportToExcel = async (data, filename, tickerInfo = null) => {
    if (!data || data.length === 0) {
        console.warn('No data to export');
        return;
    }

    try {
        // Dynamically import xlsx to reduce bundle size
        const XLSX = await import('xlsx');

        // Prepare data for worksheet
        const worksheetData = data.map(row => ({
            Date: row.time,
            Open: row.open,
            High: row.high,
            Low: row.low,
            Close: row.close,
            ...(row.volume !== undefined && { Volume: row.volume })
        }));

        // Create worksheet
        const worksheet = XLSX.utils.json_to_sheet(worksheetData);

        // Create workbook
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, 'Price Data');

        // Add ticker info sheet if available
        if (tickerInfo) {
            const infoData = [
                { Field: 'Ticker', Value: tickerInfo.ticker },
                { Field: 'Name', Value: tickerInfo.long_name || 'N/A' },
                { Field: 'Sector', Value: tickerInfo.sector || 'N/A' },
                { Field: 'Industry', Value: tickerInfo.industry || 'N/A' },
                { Field: 'Market Cap', Value: tickerInfo.market_cap || 'N/A' },
                { Field: 'Current Price', Value: tickerInfo.current_price || 'N/A' },
                { Field: 'Export Date', Value: new Date().toISOString() }
            ];
            const infoSheet = XLSX.utils.json_to_sheet(infoData);
            XLSX.utils.book_append_sheet(workbook, infoSheet, 'Info');
        }

        // Generate and download
        XLSX.writeFile(workbook, filename);
    } catch (error) {
        console.error('Failed to export Excel:', error);
        // Fallback to CSV
        exportToCSV(data, filename.replace('.xlsx', '.csv'), tickerInfo);
    }
};

/**
 * Export chart as PNG image
 * @param {HTMLElement} chartElement - Chart container element
 * @param {string} filename - Name of the file to download
 */
export const exportChartAsImage = async (chartElement, filename) => {
    if (!chartElement) {
        console.warn('No chart element provided');
        return;
    }

    try {
        // Dynamically import html2canvas
        const html2canvas = (await import('html2canvas')).default;

        // Capture the chart
        const canvas = await html2canvas(chartElement, {
            backgroundColor: '#0b0e14',
            scale: 2, // Higher quality
            logging: false
        });

        // Convert to blob and download
        canvas.toBlob((blob) => {
            downloadBlob(blob, filename);
        });
    } catch (error) {
        console.error('Failed to export chart image:', error);
        message.error('Failed to export chart. Please try again.');
    }
};

/**
 * Helper function to download a blob
 * @param {Blob} blob - Blob to download
 * @param {string} filename - Name of the file
 */
const downloadBlob = (blob, filename) => {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
};

/**
 * Generate filename with timestamp
 * @param {string} ticker - Ticker symbol
 * @param {string} extension - File extension (.csv, .xlsx, .png)
 * @returns {string} Generated filename
 */
export const generateFilename = (ticker, extension) => {
    const timestamp = new Date().toISOString().split('T')[0];
    return `${ticker}_${timestamp}${extension}`;
};
