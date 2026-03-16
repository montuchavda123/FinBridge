const StudentProfile = require('../models/StudentProfile');
const CompanyProfile = require('../models/CompanyProfile');
const User = require('../models/User');
const catchAsync = require('../utils/catchAsync');
const AppError = require('../utils/appError');

exports.updateProfile = catchAsync(async (req, res, next) => {
  const { role } = req.user;
  
  // Filter out unwanted fields
  const filterObj = (obj, ...allowedFields) => {
    const newObj = {};
    Object.keys(obj).forEach(el => {
      if (allowedFields.includes(el)) newObj[el] = obj[el];
    });
    return newObj;
  };

  let updatedProfile;

  if (role === 'student') {
    const filteredBody = filterObj(req.body, 'skills', 'education', 'experience', 'resumeUrl', 'profileCompleted');
    updatedProfile = await StudentProfile.findOneAndUpdate(
      { user: req.user._id },
      filteredBody,
      { new: true, runValidators: true }
    );
  } else if (role === 'company') {
    const filteredBody = filterObj(req.body, 'companyName', 'description', 'location', 'website', 'logoUrl');
    updatedProfile = await CompanyProfile.findOneAndUpdate(
      { user: req.user._id },
      filteredBody,
      { new: true, runValidators: true }
    );
  }

  res.status(200).json({
    status: 'success',
    data: {
      profile: updatedProfile
    }
  });
});
