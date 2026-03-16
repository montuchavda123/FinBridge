const mongoose = require('mongoose');

const interviewScheduleSchema = new mongoose.Schema({
  application: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Application',
    required: true
  },
  date: {
    type: Date,
    required: [true, 'Please provide an interview date and time']
  },
  link: {
    type: String, // e.g., Zoom/Google Meet link or physical location
    required: [true, 'Please provide an interview link or location']
  },
  status: {
    type: String,
    enum: ['Scheduled', 'Completed', 'Cancelled'],
    default: 'Scheduled'
  }
}, { timestamps: true });

module.exports = mongoose.model('InterviewSchedule', interviewScheduleSchema);
