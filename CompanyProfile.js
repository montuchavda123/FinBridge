const mongoose = require('mongoose');

const companyProfileSchema = new mongoose.Schema({
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    unique: true
  },
  companyName: {
    type: String,
    required: [true, 'Please provide the company name']
  },
  description: {
    type: String
  },
  location: {
    type: String
  },
  website: {
    type: String
  },
  logoUrl: {
    type: String // Path to uploaded file
  }
}, { timestamps: true });

module.exports = mongoose.model('CompanyProfile', companyProfileSchema);
