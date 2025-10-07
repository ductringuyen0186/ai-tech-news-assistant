import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date) {
  try {
    // Handle different date formats
    let dateObj: Date;
    
    if (date instanceof Date) {
      dateObj = date;
    } else if (typeof date === 'string') {
      // If date string doesn't end with Z, assume it's UTC and add Z
      const dateString = date.endsWith('Z') ? date : `${date}Z`;
      dateObj = new Date(dateString);
      
      // Check if date is valid
      if (isNaN(dateObj.getTime())) {
        // Try parsing without Z modification
        dateObj = new Date(date);
        if (isNaN(dateObj.getTime())) {
          return date; // Return original string if parsing fails
        }
      }
    } else {
      return String(date);
    }
    
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(dateObj);
  } catch (error) {
    console.error('Error formatting date:', error, date);
    return String(date);
  }
}

export function truncateText(text: string, maxLength: number) {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}
