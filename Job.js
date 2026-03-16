const mongoose = require('mongoose');

const jobSchema = new mongoose.Schema({
  company: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  title: {
    type: String,
    required: [true, 'A job must have a title']
  },
  description: {
    type: String,
    required: [true, 'A job must have a description']
  },
  requirements: [{
    type: String
  }],
  skillsRequired: [{
    type: String
  }],
  location: {
    type: String,
    required: [true, 'A job must specify a location']
  },
  salaryRange: {
    type: String
  },
  jobType: {
    type: String,
    enum: ['Full-time', 'Part-time', 'Contract', 'Internship'],
    default: 'Full-time'
  },
  status: {
    type: String,
    enum: ['Open', 'Closed'],
    default: 'Open'
  }
}, { timestamps: true });

module.exports = mongoose.model('Job', jobSchema);
