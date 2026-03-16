const express = require('express');
const multer = require('multer');
const path = require('path');
const AppError = require('../utils/appError');
const { protect } = require('../middlewares/authMiddleware');

const router = express.Router();

// Multer storage config
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, 'uploads/');
  },
  filename: function (req, file, cb) {
    const ext = path.extname(file.originalname);
    cb(null, `${file.fieldname}-${req.user._id}-${Date.now()}${ext}`);
  }
});

const multerFilter = (req, file, cb) => {
  if (file.mimetype.startsWith('image') || file.mimetype === 'application/pdf') {
    cb(null, true);
  } else {
    cb(new AppError('Not an image or PDF! Please upload only images or PDF files.', 400), false);
  }
};

const upload = multer({
  storage: storage,
  fileFilter: multerFilter,
  limits: {
    fileSize: 5 * 1024 * 1024 // 5MB limit
  }
});

// Route for file upload
router.post('/', protect, upload.single('file'), (req, res, next) => {
  if (!req.file) {
    return next(new AppError('Please provide a file to upload', 400));
  }

  const fileUrl = `${req.protocol}://${req.get('host')}/uploads/${req.file.filename}`;

  res.status(200).json({
    status: 'success',
    data: {
      url: fileUrl
    }
  });
});

module.exports = router;
