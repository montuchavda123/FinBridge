const mongoose = require('mongoose');

const applicationSchema = new mongoose.Schema({
  job: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Job',
    required: true
  },
  student: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  resumeUsed: {
    type: String,
    required: [true, 'Application must include a resume link or file path']
  },
  status: {
    type: String,
    enum: ['Applied', 'Shortlisted', 'Interviewing', 'Rejected', 'Hired'],
    default: 'Applied'
  }
}, { timestamps: true });

// Prevent multiple applications by the same student to the same job
applicationSchema.index({ job: 1, student: 1 }, { unique: true });

module.exports = mongoose.model('Application', applicationSchema);
